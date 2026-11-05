"""Environment readiness handshake for the host's setup agent.

The host supplies the agent, not the model API. This module verifies its work.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from .sources import lock, verify

IMPORTS = {
    'arbor_tree': ['pydantic_settings'],
    'claw_debate': ['researchclaw.pipeline.debate', 'researchclaw.prompts'],
    'claw_discuss_select': ['researchclaw.pipeline.debate', 'researchclaw.pipeline.tournament', 'researchclaw.prompts'],
    'claw_novelty': ['researchclaw.literature.novelty'],
    'claw_stage': ['researchclaw.config', 'researchclaw.pipeline.executor', 'researchclaw.adapters'],
    'coi_chain': ['agents'],
    'coi_review': ['agents'],
}


def check_environment(root, key, adapter, job, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    descriptor_path = root / '.environments' / key / 'ready.json'
    setup_request = {'status': 'needs_environment', 'upstream': key, 'adapter': adapter,
        'source_commit': lock(root)[key]['sha'], 'repository': lock(root)[key]['url'],
        'required_imports': IMPORTS[adapter], 'source': job.get('source'),
        'descriptor_path': str(descriptor_path), 'skill': 'skills/mai-setup-environment/SKILL.md',
        'scope': 'prepare environment only; do not generate research results or approve novelty'}
    try:
        descriptor = json.loads(descriptor_path.read_text()) if descriptor_path.exists() else {}
        if descriptor and descriptor.get('source_commit') != setup_request['source_commit']:
            raise ValueError('Prepared environment is for a different source revision')
        source = verify(root, key, job.get('source') or descriptor.get('source'))
        python = job.get('python') or descriptor.get('python') or sys.executable
        env = {k: v for k, v in os.environ.items()
               if not any(x in k.upper() for x in ('TOKEN', 'SECRET', 'PASSWORD', 'API_KEY'))}
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        # Import from the pinned source and stage's interpreter; no inference/network probe.
        program = 'import sys,importlib;sys.path.insert(0,sys.argv[1]);[importlib.import_module(m) for m in sys.argv[2:]]'
        probe = subprocess.run([python, '-c', program, str(source), *IMPORTS[adapter]],
                               cwd=output, env=env, capture_output=True, text=True, timeout=30)
        (output / 'environment-check.log').write_text(probe.stdout + probe.stderr)
        if probe.returncode:
            raise RuntimeError('Import check failed; see environment-check.log')
        record = dict(status='ready', upstream=key, source_commit=setup_request['source_commit'],
                      source=str(source), python=str(python), checked_at=time.time(),
                      imports=IMPORTS[adapter], model_ready='not_checked', experiment_ready='not_checked')
        (output / 'environment.json').write_text(json.dumps(record, indent=2))
        return record
    except Exception as exc:
        setup_request['reason'] = f'{type(exc).__name__}: {exc}'
        (output / 'environment-request.json').write_text(json.dumps(setup_request, indent=2))
        return setup_request
