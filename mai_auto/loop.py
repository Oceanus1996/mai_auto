"""Bounded, resumable orchestration. Research methods remain in native workers."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid
from .runner import run

STAGES = ('generate', 'debate', 'minimum_check', 'revise', 'archive')


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def bind(value, context):
    """Exact JSON-pointer substitution, never eval, shell, or prompt rewriting."""
    if isinstance(value, dict):
        if set(value) == {'$ref'}:
            pointer = value['$ref']
            if not isinstance(pointer, str) or not pointer.startswith('/'):
                raise ValueError('Reference must be a JSON pointer beginning with /')
            result = context
            for key in pointer[1:].split('/'):
                key = key.replace('~1', '/').replace('~0', '~')
                result = result[int(key)] if isinstance(result, list) else result[key]
            return copy.deepcopy(result)
        return {k: bind(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [bind(v, context) for v in value]
    return value


def execute(root, spec, context, folder, timeout):
    if 'job' in spec:
        job = bind(spec['job'], context)
        job['timeout'] = min(float(job.get('timeout', timeout)), timeout)
        record = run(root, job)
        save(folder / 'native-record.json', record)
        if record['status'] != 'completed':
            raise RuntimeError('Native invocation: ' + record['status'] + '; setup_request=' + str(record.get('setup_request', '')))
        return json.loads((root / 'runs' / record['run_id'] / 'result.json').read_text())
    command = spec['command']
    # Workers receive a complete context and a unique output path. No shell expansion.
    save(folder / 'request.json', context)
    env = {k: v for k, v in os.environ.items()
           if not any(s in k.upper() for s in ('TOKEN', 'SECRET', 'PASSWORD', 'API_KEY'))}
    for key in spec.get('pass_env', []):
        if key in os.environ:
            env[key] = os.environ[key]
    with (folder / 'stdout.log').open('w') as out, (folder / 'stderr.log').open('w') as err:
        process = subprocess.Popen(command + [str(folder / 'request.json'), str(folder / 'result.json')],
                                   cwd=root, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise RuntimeError('Worker timed out')
    if code:
        raise RuntimeError(f'Worker exited {code}; see stderr.log')
    return json.loads((folder / 'result.json').read_text(encoding='utf-8'))


def validate(config):
    for name in ('max_rounds', 'max_calls'):
        if type(config.get(name)) is not int or config[name] < 1:
            raise ValueError(name + ' must be a positive integer')
    for name in ('max_seconds', 'stage_timeout'):
        value = config.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(name + ' must be finite and positive')
    for stage in STAGES:
        spec = config.get('stages', {}).get(stage)
        if not isinstance(spec, dict) or (('job' in spec) + ('command' in spec)) != 1:
            raise ValueError(f'{stage}: configure exactly one native job or worker command')
        if 'command' in spec and (not isinstance(spec['command'], list) or not spec['command'] or
                                 any(not isinstance(x, str) or not x for x in spec['command'])):
            raise ValueError(stage + ': command must be a nonempty argv array')


def check_result(stage, result, root):
    if not isinstance(result, dict):
        raise ValueError('Stage output must be a JSON object')
    if stage == 'minimum_check':
        if result.get('verdict') not in ('supported', 'refuted', 'inconclusive'):
            raise ValueError('minimum_check requires a verdict')
        if not isinstance(result.get('evidence'), list) or not result['evidence']:
            raise ValueError('minimum_check requires actual evidence files')
        hashes = []
        for item in result['evidence']:
            if not isinstance(item, str):
                raise ValueError('Evidence entries must be file paths')
            path = (root / item).resolve()
            path.relative_to(root)
            hashes.append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        result = dict(result, evidence_hashes=hashes)
    if stage == 'revise':
        if result.get('action') not in ('continue', 'stop', 'blocked') or not result.get('reason'):
            raise ValueError('revise requires action and reason')
        if result['action'] == 'continue' and not isinstance(result.get('next_input'), dict):
            raise ValueError('continue requires next_input object')
    return result

