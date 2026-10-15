"""HTTP-only workflow, one ticket, exact-query continuation, bounded polling."""
import hashlib
import json
import os
from pathlib import Path
import time
from auth import get_auth
from local_support import private_dir, save_private
from transport import call


def run(curl, work, info, args):
    work = private_dir(work)
    lock = work/'run.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print('TASK_LOCKED: another run or interrupted process; verify its PID before removing run.lock.')
        return 2
    with os.fdopen(fd, 'w') as f:
        f.write(str(os.getpid()))
    started = time.monotonic()
    report = {'steps': []}
    def log(stage, values):
        entry = {'stage':stage,'elapsed_seconds':round(time.monotonic()-started,3),**values}
        report['steps'].append(entry)
        save_private(work/'diagnostic.json', report)
        print(json.dumps(entry), flush=True)
    try:
        # Completed result is local and requires no repeated billed request.
        if args.resume and (work/'result.json').exists():
            print('SUCCESS: existing result.json; no network request.')
            return 0
        auth = get_auth(curl)
        metrics, body = call(curl, auth, '/mcp-tools')
        log('identity', metrics)
        if metrics.get('http_code') != 200 or metrics.get('curl_exit') != 0:
            return 2
        private = work/'private-task.json'
        if args.resume:
            if not private.exists():
                raise ValueError('NO_CONTINUATION_STATE: do not create another ticket automatically')
            saved = json.loads(private.read_text(encoding='utf-8'))
            query = saved['query']
        else:
            if (work/'attempt.json').exists():
                raise ValueError('EXISTING_ATTEMPT: use --resume --work-dir')
            file, mime, size, duration, digest = info
            query = {'video_type':1,'limit':args.limit}
            if args.date_from:
                query.update(date_from=args.date_from,date_to=args.date_to)
            save_private(work/'attempt.json', {'ticket_request_started':True})
            metrics, body = call(curl, auth, '/media/upload-ticket', payload={
                'media_type':'video' if mime.startswith('video/') else 'image',
                'content_type':mime,'file_size':size})
            log('ticket', metrics)
            data = body.get('data', {})
            if metrics.get('http_code') != 200 or not data.get('media_token'):
                return 2
            query['media_token'] = data['media_token']
            saved = {'query':query,'file':str(file),'sha256':digest,'mime':mime,
                     'upload_started':False,'upload_expires_at':data.get('upload',{}).get('expires_at')}
            save_private(private, saved)
        token = query['media_token']
        metrics, body = call(curl, auth, '/media/status', payload={'media_token':token})
        state = body.get('data',{}).get('state')
        log('task', {**metrics,'state':state})
        if metrics.get('http_code') != 200 or state not in ('issued','queued','running','ready'):
            return 2
        if state == 'issued' and not saved.get('upload_started'):
            file = Path(saved['file'])
            if hashlib.sha256(file.read_bytes()).hexdigest() != saved['sha256']:
                raise ValueError('SOURCE_FILE_CHANGED')
            # Mark before upload: restart never resends an uncertain upload.
            saved['upload_started'] = True
            save_private(private,saved)
            log('upload_started', {'file_bytes':file.stat().st_size})
            metrics, body = call(curl, auth, '/media/upload-relay', token=token,
                                 file=file, mime=saved['mime'])
            data = body.get('data',{})
            log('upload',{**metrics,**{k:data.get(k) for k in ('uploaded','receive_ms','oss_ms','total_ms')}})
        # Same saved query verifies an uncertain upload and preserves billing identity.
        deadline = time.monotonic()+300
        while time.monotonic() < deadline:
            metrics, body = call(curl, auth, '/media/search', payload=query)
            data = body.get('data',{}); meta = body.get('meta',{})
            log('search',{**metrics,'state':data.get('state'),'count':meta.get('returned_count')})
            if metrics.get('http_code') == 200 and isinstance(data.get('items'),list):
                save_private(work/'result.json',body)
                log('complete',{'returned_count':len(data['items'])})
                print('SUCCESS: result.json and diagnostic.json saved.')
                return 0
            if metrics.get('http_code') != 200 or data.get('state') != 'processing':
                return 2
            time.sleep(min(15,max(2,float(data.get('retry_after_seconds',5)))))
        log('stop',{'error':'PROCESSING_WAIT_LIMIT','action':'resume same work-dir'})
        return 2
    except Exception as exc:
        log('local_error',{'error':str(exc) if type(exc) is ValueError else type(exc).__name__})
        return 2
    finally:
        lock.unlink(missing_ok=True)
