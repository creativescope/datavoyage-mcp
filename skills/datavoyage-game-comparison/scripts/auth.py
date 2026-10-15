"""Own OAuth session: browser PKCE with loopback callback; never reads MCP caches."""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser
from local_support import curl_path, save_private, state_root
from transport import call

ISSUER = 'https://api.datavoyage.cn'
RESOURCE = 'https://mcpapi.datavoyage.cn/mcp'


def request(curl, path, **kwargs):
    metrics, body = call(curl, '', '', url=ISSUER + path, **kwargs)
    if metrics.get('curl_exit') != 0 or metrics.get('http_code') not in (200, 201):
        raise ValueError('OAUTH_REQUEST_FAILED')
    return body


def persist(value):
    token = value.get('access_token')
    if not isinstance(token, str) or not token:
        raise ValueError('OAUTH_TOKEN_MISSING')
    value['expires_at'] = time.time() + float(value.get('expires_in', 0))
    save_private(state_root() / 'auth.json', value)


def get_auth(curl):
    token = os.environ.get('AUTH_TOKEN', '').strip()
    if token:
        return token
    path = state_root() / 'auth.json'
    if not path.is_file():
        raise ValueError('LOGIN_REQUIRED: run scripts/auth.py login')
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('expires_at', 0) > time.time() + 60:
        return value['access_token']
    if not value.get('refresh_token'):
        raise ValueError('LOGIN_REQUIRED')
    body = request(curl, '/oauth/token', form={
        'grant_type': 'refresh_token', 'client_id': value['client_id'],
        'refresh_token': value['refresh_token'], 'resource': RESOURCE})
    body['client_id'] = value['client_id']
    body.setdefault('refresh_token', value['refresh_token'])
    persist(body)
    return body['access_token']


def login(curl):
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            valid = (parsed.path == '/callback' and
                     secrets.compare_digest(query.get('state', [''])[0], state))
            self.send_response(200 if valid else 400)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            if valid:
                received.update(code=query.get('code', [''])[0], error=bool(query.get('error')))
            self.wfile.write(b'Return to your assistant.' if valid else b'Invalid callback.')

    with HTTPServer(('127.0.0.1', 0), Handler) as server:
        server.timeout = 1
        redirect = 'http://127.0.0.1:%d/callback' % server.server_port
        client_file = state_root() / 'client.json'
        if client_file.exists():
            client = json.loads(client_file.read_text(encoding='utf-8'))
        else:
            client = request(curl, '/oauth/register', payload={
                'client_name': 'DataVoyage Skills', 'application_type': 'native',
                'redirect_uris': [], 'token_endpoint_auth_method': 'none',
                'grant_types': ['authorization_code', 'refresh_token'], 'response_types': ['code']})
            save_private(client_file, {'client_id': client['client_id']})
        url = ISSUER + '/oauth/authorize?' + urlencode({
            'response_type': 'code', 'client_id': client['client_id'], 'redirect_uri': redirect,
            'scope': 'mcp:use', 'state': state, 'code_challenge': challenge,
            'code_challenge_method': 'S256', 'resource': RESOURCE})
        print('LOGIN: Complete login and authorization in the browser. Waiting up to 10 minutes.', flush=True)
        if not webbrowser.open(url):
            print('Open this authorization URL locally (do not include it in reports):\n' + url, flush=True)
        deadline = time.monotonic() + 600
        while not received and time.monotonic() < deadline:
            server.handle_request()
        if received.get('error') or not received.get('code'):
            raise ValueError('LOGIN_CANCELLED_OR_TIMED_OUT')
        body = request(curl, '/oauth/token', form={
            'grant_type': 'authorization_code', 'client_id': client['client_id'],
            'code': received['code'], 'redirect_uri': redirect, 'code_verifier': verifier,
            'resource': RESOURCE})
        body['client_id'] = client['client_id']
        persist(body)
    print('LOGIN_OK', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['login', 'status', 'logout'])
    args = parser.parse_args()
    try:
        curl = curl_path()
        if args.action == 'login':
            login(curl)
        elif args.action == 'status':
            auth = get_auth(curl)
            metrics, body = call(curl, auth, '/mcp-tools')
            print(json.dumps({'authenticated': metrics.get('http_code') == 200, **metrics}))
            return 0 if metrics.get('http_code') == 200 else 2
        else:
            path = state_root() / 'auth.json'
            if path.exists():
                value = json.loads(path.read_text(encoding='utf-8'))
                request(curl, '/oauth/revoke', form={
                    'token': value.get('refresh_token') or value['access_token'],
                    'client_id': value['client_id']})
                path.unlink()
            print('LOGOUT_OK: own stored authorization only; AUTH_TOKEN environment is unchanged.')
        return 0
    except Exception as exc:
        # Never print exception text originating from HTTP/JSON libraries.
        print('AUTH_FAILED: ' + (str(exc) if type(exc) is ValueError else type(exc).__name__))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
