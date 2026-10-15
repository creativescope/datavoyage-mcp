"""Portable dependencies, private local state. No network."""
import csv
import json
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

