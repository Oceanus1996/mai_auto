import argparse
import json
from pathlib import Path
from .sources import lock, verify, bootstrap
from .runner import run, run_parallel
from .claw_workflow import run_claw_workflow, record_novelty_review


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
    loop = commands.add_parser('loop')
    loop.add_argument('config', type=Path)
    loop.add_argument('--resume', type=Path)
    loop.add_argument('--retry', action='store_true')
    review = commands.add_parser('novelty-review')
    review.add_argument('run_dir', type=Path)
    review.add_argument('decision', choices=['continue', 'differentiate', 'reject', 'need_evidence'])
    review.add_argument('--reason', required=True)
    review.add_argument('--reviewer', required=True)
    args = parser.parse_args()
    if args.command == 'novelty-review':
        print(json.dumps(record_novelty_review(args.run_dir, args.decision, args.reason, args.reviewer), ensure_ascii=False, indent=2))
        return
    if args.command == 'loop':
        state = run_claw_workflow(args.root, json.loads(args.config.read_text()), args.resume, args.retry)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        if state['status'] == 'blocked' or state.get('decision') == 'blocked':
            raise SystemExit(1)
        return
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
