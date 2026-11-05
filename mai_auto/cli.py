import argparse
import json
from pathlib import Path
from .sources import lock, verify, bootstrap
from .runner import run, run_parallel


def main():
    parser = argparse.ArgumentParser(description='Pinned native research skill bridges')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor')
    boot = commands.add_parser('bootstrap')
    boot.add_argument('sources', nargs='+')
    one = commands.add_parser('run')
    one.add_argument('job', type=Path)
    batch = commands.add_parser('batch')
    batch.add_argument('jobs', type=Path)
    batch.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    if args.command == 'bootstrap':
        bootstrap(args.root, args.sources)
        return
    if args.command == 'doctor':
        for key in lock(args.root):
            try:
                path = verify(args.root, key)
                print(key, 'PIN_OK (dependencies/model not checked)', path)
            except Exception as exc:
                print(key, 'BLOCKED', str(exc))
        return
    if args.command == 'run':
        records = [run(args.root, json.loads(args.job.read_text()))]
    else:
        records = run_parallel(args.root, json.loads(args.jobs.read_text()), args.workers)
    print(json.dumps(records, indent=2))
    if any(r['status'] != 'completed' for r in records):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
