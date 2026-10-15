"""Portable entry point. --check-only is offline; --resume never creates tickets."""
import argparse
import datetime
import json
import time
from pathlib import Path
from local_support import curl_path, media_info, state_root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file')
    parser.add_argument('--work-dir')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--date-from')
    parser.add_argument('--date-to')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    try:
        if args.cleanup:
            if not args.work_dir or args.resume or args.file:
                raise ValueError('CLEANUP_REQUIRES_ONLY_WORK_DIR')
            work = Path(args.work_dir).resolve(strict=True)
            if not (work/'attempt.json').exists():
                raise ValueError('NOT_A_TASK_DIRECTORY')
            (work/'private-task.json').unlink(missing_ok=True)
            print('PRIVATE_TASK_REMOVED: local continuation disabled; server data unchanged.')
            return 0
        curl = curl_path()
        if args.resume:
            if not args.work_dir or args.file or args.date_from or args.date_to or args.limit != 10:
                raise ValueError('RESUME_USE_ONLY_WORK_DIR')
            work = Path(args.work_dir).resolve(strict=True)
            info = None
        else:
            if not args.file:
                raise ValueError('FILE_REQUIRED')
            info = media_info(args.file)
            if not 1 <= args.limit <= 50 or bool(args.date_from) != bool(args.date_to):
                raise ValueError('INVALID_QUERY')
            if args.date_from:
                span = (datetime.date.fromisoformat(args.date_to)-datetime.date.fromisoformat(args.date_from)).days
                if not 0 <= span <= 180:
                    raise ValueError('INVALID_DATE_RANGE')
            # State stays outside shared workspaces by default.
            work = Path(args.work_dir).resolve() if args.work_dir else state_root()/'tasks'/str(time.time_ns())
        print(json.dumps({'stage':'local_preflight','work_dir':str(work),
                          'file_bytes':info[2] if info else None,
                          'duration_seconds':info[3] if info else None,
                          'video_validation':('local_checked' if info[3] is not None else 'deferred_to_server') if info and info[1].startswith('video/') else 'not_applicable',
                          'check_only':args.check_only}), flush=True)
        if args.check_only:
            return 0
        from search_media import run
        return run(curl, work, info, args)
    except Exception as exc:
        print(json.dumps({'stage':'local_error', 'error':str(exc) if type(exc) is ValueError else type(exc).__name__}), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
