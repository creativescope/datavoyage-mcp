"""Direct MCP client for chart queries; no WorkBuddy connector required."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time
from auth import get_auth
from local_support import curl_path, private_dir, save_private, state_root
from transport import quote

ALLOWED = {'get_context', 'get_store_game_rank_filter', 'get_store_game_rank',
           'get_store_game_rank_trend', 'get_store_first_seen_games',
           'search_games', 'resolve_game_by_identifier'}


def decode_reply(raw, request_id):
    try:
        packets = [json.loads(raw)]
    except ValueError:
        packets = []
        for event in raw.replace('\r\n', '\n').split('\n\n'):
            data = '\n'.join(line[5:].lstrip(' ') for line in event.splitlines() if line.startswith('data:'))
            if data:
                try:
                    packets.append(json.loads(data))
                except ValueError:
                    continue
    for packet in packets:
        if isinstance(packet, dict) and packet.get('id') == request_id:
            if 'error' in packet:
                raise ValueError('MCP_RPC_ERROR')
            if isinstance(packet.get('result'), dict):
                return packet['result']
    raise ValueError('MCP_RESPONSE_MISSING')


class Client:
    def __init__(self, curl, token):
        self.curl, self.token = curl, token
        self.session = None
        self.version = None
        self.counter = 0

    def request(self, method, params=None, notify=False):
        self.counter += 1
        packet = {'jsonrpc':'2.0','method':method}
        if not notify:
            packet['id'] = self.counter
        if params is not None:
            packet['params'] = params
        headers = ['Content-Type: application/json','Accept: application/json, text/event-stream',
                   'Authorization: Bearer '+self.token]
        if self.session:
            headers.append('Mcp-Session-Id: '+self.session)
        if self.version:
            headers.append('MCP-Protocol-Version: '+self.version)
        config = ['url = "https://mcpapi.datavoyage.cn/mcp"']
        config += ['header = '+quote(h) for h in headers]
        config += ['data = '+quote(json.dumps(packet))]
        with tempfile.TemporaryDirectory(prefix='dv-chart-') as d:
            folder = private_dir(d)
            response, head = folder/'response', folder/'headers'
            argv = [self.curl,'-q','--config','-','--silent','--noproxy','*','--proto','=https',
                    '--connect-timeout','15','--max-time','90','--output',str(response),
                    '--dump-header',str(head),'--write-out','%{http_code}']
            completed = subprocess.run(argv,input='\n'.join(config),text=True,encoding='utf-8',
                                       errors='replace',capture_output=True,timeout=105)
            status = completed.stdout.strip()
            if completed.returncode:
                raise ValueError('NETWORK_ERROR: no automatic retry; query may have executed')
            if status not in ('200','202','204'):
                raise ValueError('HTTP_'+status if status.isdigit() else 'HTTP_ERROR')
            if head.exists():
                for line in head.read_text(encoding='utf-8').splitlines():
                    key, sep, value = line.partition(':')
                    if sep and key.lower() == 'mcp-session-id':
                        self.session = value.strip()
            if notify:
                return {}
            return decode_reply(response.read_text(encoding='utf-8'),self.counter)

    def initialize(self):
        reply = self.request('initialize',{'protocolVersion':'2025-03-26',
            'capabilities':{},'clientInfo':{'name':'datavoyage-charts-skill','version':'1.0.1'}})
        self.version = reply.get('protocolVersion')
        if self.version not in ('2025-03-26','2025-06-18','2025-11-25'):
            raise ValueError('UNSUPPORTED_PROTOCOL_VERSION')
        self.request('notifications/initialized',notify=True)

    def tools(self):
        result, cursor, seen = [], None, set()
        for _ in range(20):
            page = self.request('tools/list',{'cursor':cursor} if cursor else {})
            result.extend(t for t in page.get('tools',[]) if t.get('name') in ALLOWED)
            cursor = page.get('nextCursor')
            if not cursor:
                return result
            if cursor in seen:
                break
            seen.add(cursor)
        raise ValueError('TOOL_LIST_PAGINATION_ERROR')


def unpack(result):
    if result.get('isError'):
        raise ValueError('MCP_TOOL_ERROR')
    structured = result.get('structuredContent')
    if isinstance(structured,dict):
        return structured
    for block in result.get('content',[]):
        if block.get('type') == 'text':
            try:
                value = json.loads(block.get('text',''))
                if isinstance(value,dict):
                    return value
            except ValueError:
                pass
    raise ValueError('TOOL_RESULT_FORMAT_ERROR')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog',action='store_true')
    parser.add_argument('--tool',choices=sorted(ALLOWED))
    parser.add_argument('--args',help='Inline UTF-8 JSON object of non-secret query arguments')
    parser.add_argument('--args-file',help='UTF-8 JSON file of non-secret query arguments')
    parser.add_argument('--output',help='New result file; existing files are never overwritten')
    args = parser.parse_args()
    try:
        if args.catalog == bool(args.tool) or (args.catalog and (args.args or args.args_file)):
            raise ValueError('CHOOSE_CATALOG_OR_TOOL')
        if args.args and args.args_file:
            raise ValueError('CHOOSE_ARGS_OR_ARGS_FILE')
        if args.args:
            values = json.loads(args.args)
        elif args.args_file:
            values = json.loads(Path(args.args_file).read_text(encoding='utf-8-sig'))
        else:
            values = {}
        if not isinstance(values,dict):
            raise ValueError('ARGUMENTS_MUST_BE_OBJECT')
        output = Path(args.output).resolve() if args.output else state_root()/'charts'/str(time.time_ns())/'result.json'
        if output.exists():
            raise ValueError('OUTPUT_EXISTS: read the saved result instead of rerunning')
        private_dir(output.parent)
        # Marker blocks blind retry even if the HTTP response is lost.
        marker = output.with_name(output.name+'.attempt')
        if marker.exists():
            raise ValueError('PREVIOUS_ATTEMPT: inspect outcome before another query')
        curl = curl_path()
        client = Client(curl,get_auth(curl))
        client.initialize()
        catalog = client.tools()
        if args.catalog:
            body = {'tools':catalog}
        else:
            tool = next((t for t in catalog if t['name']==args.tool),None)
            if not tool:
                raise ValueError('TOOL_UNAVAILABLE')
            schema = tool.get('inputSchema',{})
            if not set(schema.get('required',[])) <= values.keys():
                raise ValueError('REQUIRED_ARGUMENT_MISSING')
            if set(values)-set(schema.get('properties',{})):
                raise ValueError('UNKNOWN_ARGUMENT')
            with marker.open('x',encoding='utf-8') as f:
                json.dump({'tool':args.tool,'started':True},f)
            print(json.dumps({'status':'querying','output':str(output)}),flush=True)
            body = unpack(client.request('tools/call',{'name':args.tool,'arguments':values}))
        save_private(output,body)
        meta = body.get('meta') or {}
        code = meta.get('error_code') if isinstance(meta,dict) else None
        print(json.dumps({'output':str(output),'error_code':code,'status':'error' if code else 'saved'}),flush=True)
        return 2 if code else 0
    except Exception as exc:
        print(json.dumps({'status':'stopped','error':str(exc) if type(exc) is ValueError else type(exc).__name__}),flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
