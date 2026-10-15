"""Bounded direct curl relay with identity/task preflight; never creates tickets."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from local_support import private_dir
from urllib.parse import urlencode, urlparse

BASE = "https://mcpapi.datavoyage.cn"
METRICS = ("http_code", "size_upload", "speed_upload", "time_connect", "time_appconnect", "time_starttransfer", "time_total", "exitcode")

def quote(value):
    if any(c in str(value) for c in ("\r", "\n", "\0")):
        raise ValueError("Invalid header or path")
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'

def call(curl, auth, route, token=None, payload=None, file=None, mime=None, url=None, form=None):
    # Secrets only reach curl stdin, never argv, files or diagnostic output.
    target = url or BASE + route
    parsed = urlparse(target)
    if parsed.scheme != "https" or parsed.netloc not in ("mcpapi.datavoyage.cn", "api.datavoyage.cn"):
        raise ValueError("UNTRUSTED_ENDPOINT")
    config = ["url = " + quote(target)]
    if auth:
        config.append("header = " + quote("Authorization: Bearer " + auth))
    if token:
        config.append("header = " + quote("X-Media-Token: " + token))
    if file:
        config += ["header = " + quote("Content-Type: " + mime), 'header = "Expect: 100-continue"',
                   "data-binary = " + quote("@" + str(file))]
    elif form is not None:
        config += ['header = "Content-Type: application/x-www-form-urlencoded"', "data = " + quote(urlencode(form))]
    elif payload is not None:
        config += ['header = "Content-Type: application/json"', "data = " + quote(json.dumps(payload))]
    with tempfile.TemporaryDirectory(prefix="dv-relay-") as folder:
        private_dir(folder)
        response = Path(folder) / "response.json"
        args = [curl, "-q", "--config", "-", "--silent", "--noproxy", "*", "--proto", "=https",
                "--connect-timeout", "15", "--max-time", "600" if file else "30",
                "--expect100-timeout", "2", "--output", str(response), "--write-out", "%{json}"]
        result = subprocess.run(args, input="\n".join(config), text=True, encoding="utf-8", errors="replace",
                                capture_output=True, timeout=615 if file else 45)
        try:
            metrics = json.loads(result.stdout)
        except ValueError:
            metrics = {}
        safe = {k: metrics.get(k) for k in METRICS}
        safe["curl_exit"] = result.returncode
        try:
            body = json.loads(response.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            body = {}
        if not isinstance(body, dict): body = {}
        meta = body.get("meta") or {}
        safe["error_code"] = meta.get("error_code") if isinstance(meta, dict) else None
        safe["request_id"] = meta.get("request_id") if isinstance(meta, dict) else None
        return safe, body
