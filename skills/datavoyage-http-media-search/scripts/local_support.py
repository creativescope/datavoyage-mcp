"""Portable dependencies, private local state and media validation. No network."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def private_dir(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('UNSAFE_STATE_DIRECTORY')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'nt':
        identity = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'],
                                  capture_output=True, text=True, check=True)
        sid = list(csv.reader(identity.stdout.splitlines()))[0][-1]
        if not re.fullmatch(r'S-1-[0-9-]+', sid):
            raise ValueError('PRIVATE_DIRECTORY_ACL_FAILED')
        result = subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r',
                                 '*' + sid + ':(OI)(CI)F'], capture_output=True)
        if result.returncode:
            raise ValueError('PRIVATE_DIRECTORY_ACL_FAILED')
    else:
        path.chmod(0o700)
    return path


def state_root():
    if sys.platform == 'win32':
        root = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    elif sys.platform == 'darwin':
        root = Path.home() / 'Library' / 'Application Support'
    else:
        root = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local' / 'state'))
    return private_dir(root / 'DataVoyage' / 'media-search')


def save_private(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('UNSAFE_STATE_FILE')
    temp = path.with_name(path.name + '.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def curl_path():
    # Prefer the native Windows TLS stack; PATH supports Homebrew on macOS.
    native = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32' / 'curl.exe'
    candidate = str(native) if os.name == 'nt' and native.is_file() else shutil.which('curl')
    if not candidate:
        raise ValueError('CURL_MISSING')
    result = subprocess.run([candidate, '-q', '--version'], capture_output=True, text=True, timeout=10)
    match = re.search(r'curl (\d+)\.(\d+)\.(\d+)', result.stdout)
    if result.returncode or not match or tuple(map(int, match.groups())) < (7, 70, 0):
        raise ValueError('CURL_7_70_REQUIRED')
    return candidate


def media_info(file):
    file = Path(file).resolve(strict=True)
    if not file.is_file():
        raise ValueError('FILE_REQUIRED')
    with file.open('rb') as stream:
        header = stream.read(4096)
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'image/png'
    elif header.startswith(b'\xff\xd8\xff'):
        mime = 'image/jpeg'
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        mime = 'image/webp'
    elif header[4:8] == b'ftyp':
        mime = 'video/quicktime' if header[8:12] == b'qt  ' else 'video/mp4'
    elif header.startswith(b'\x1aE\xdf\xa3') and b'webm' in header:
        mime = 'video/webm'
    else:
        raise ValueError('UNSUPPORTED_MEDIA_CONTENT')
    video = mime.startswith('video/')
    size = file.stat().st_size
    if not 0 < size <= (50 if video else 10) * 1024 * 1024:
        raise ValueError('FILE_SIZE_LIMIT')
    duration = None
    probe = shutil.which('ffprobe') if video else None
    if probe:
        result = subprocess.run([probe, '-v', 'error', '-show_entries',
                                 'format=duration:stream=codec_type', '-of', 'json', str(file)],
                                capture_output=True, timeout=30)
        if result.returncode:
            raise ValueError('VIDEO_PROBE_FAILED')
        info = json.loads(result.stdout)
        duration = float(info.get('format', {}).get('duration', 0))
        if not math.isfinite(duration) or not 0 < duration <= 120:
            raise ValueError('VIDEO_DURATION_LIMIT')
        if not any(s.get('codec_type') == 'video' for s in info.get('streams', [])):
            raise ValueError('VIDEO_STREAM_MISSING')
    digest = hashlib.sha256()
    with file.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return file, mime, size, duration, digest.hexdigest()
