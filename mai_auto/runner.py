"""Isolated task invocation and immutable raw artifacts; process success is not scientific success."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from .sources import verify, lock
from .environment import check_environment

ADAPTERS = {'arbor_tree': 'arbor', 'claw_debate': 'claw', 'claw_discuss_select': 'claw', 'claw_novelty': 'claw', 'claw_stage': 'claw', 'coi_review': 'coi', 'coi_chain': 'coi'}


def run(root, job):
    root = Path(root).resolve()
    adapter = job['adapter']
    key = ADAPTERS[adapter]
    run_id = uuid.uuid4().hex
    output = root / 'runs' / run_id
    output.mkdir(parents=True)
    environment = check_environment(root, key, adapter, job, output)
    if environment['status'] != 'ready':
        record = {'run_id': run_id, 'agent_id': job['agent_id'], 'adapter': adapter,
                  'status': 'blocked_environment', 'scientific_verdict': 'not_assessed',
                  'setup_request': str(output / 'environment-request.json')}
        (output / 'record.json').write_text(json.dumps(record, indent=2))
        return record
    source = environment['source']
    job = dict(job, python=environment['python'])
    request = dict(job, source=str(source), output=str(output))
    serialized = json.dumps(request, ensure_ascii=False, sort_keys=True)
    (output / 'request.json').write_text(serialized)
    record = {'run_id': run_id, 'agent_id': job['agent_id'], 'adapter': adapter,
              'upstream_sha': lock(root)[key]['sha'], 'started_at': time.time(),
              'input_sha256': hashlib.sha256(serialized.encode()).hexdigest(),
              'status': 'running', 'scientific_verdict': 'not_assessed'}
    record_path = output / 'record.json'
    record_path.write_text(json.dumps(record, indent=2))
    # Do not forward cloud credentials. Native web retrieval can still require separate setup.
    env = {k: v for k, v in os.environ.items()
           if not any(s in k.upper() for s in ('TOKEN', 'SECRET', 'PASSWORD', 'API_KEY'))}
    key_env = job.get('model', {}).get('key_env')
    if key_env and key_env in os.environ:
        env[key_env] = os.environ[key_env]
    for name in job.get('pass_env', []):
        if name in os.environ:
            env[name] = os.environ[name]
    env['PYTHONPATH'] = str(root)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        with (output / 'stdout.log').open('w') as stdout, (output / 'stderr.log').open('w') as stderr:
            process = subprocess.Popen([job.get('python', sys.executable), '-m', 'mai_auto.worker',
                        str(output / 'request.json')], cwd=output, env=env,
                        stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                code = process.wait(timeout=job.get('timeout', 300))
                record['exit_code'] = code
                record['status'] = 'completed' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                record['status'] = 'timed_out'
    except Exception as exc:
        record['status'] = 'failed'
        record['error_type'] = type(exc).__name__
    record['finished_at'] = time.time()
    record_path.write_text(json.dumps(record, indent=2))
    return record


def run_parallel(root, jobs, workers=2):
    if workers < 1:
        raise ValueError('workers must be positive')
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda job: run(root, job), jobs))
