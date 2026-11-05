"""Claw stage routing plus explicit integration gates; no new research prompts.

This is an adapted driver, not an invocation of Claw's unmodified runner.
Native jobs execute Claw stages; command hooks bridge external original agents.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid
from .loop import save, execute, check_result
from .sources import verify

ORDER = ('generate', 'novelty', 'discuss_select', 'novelty_selected', 'design', 'plan_check',
         'implement', 'resources', 'execute', 'result_check', 'analyze', 'decision', 'archive')
REQUIRED = (*ORDER, 'refine')


def route(stage, result, current, rollbacks):
    if stage in ('novelty', 'novelty_selected'):
        text = (current['discuss_select']['selected']['text'] if stage == 'novelty_selected'
                else current['generate']['text'])
        expected = hashlib.sha256(text.encode()).hexdigest()
        if result.get('claim_sha256') != expected or not isinstance(result.get('report'), dict):
            raise ValueError('Novelty report does not match candidate content')
        review = result.get('human_review')
        if not review:
            return 'awaiting_human', None
        decision = review['decision']
        if decision == 'continue':
            return ('discuss_select' if stage == 'novelty' else 'design'), None
        if decision == 'differentiate':
            return 'generate', 'pivot'
        if decision == 'reject':
            return 'stopped', None
        return 'blocked', None
    if stage == 'plan_check':
        if result.get('verdict') == 'revise':
            return 'design', 'redesign'
        if result.get('verdict') != 'pass':
            return 'blocked', None
    if stage == 'result_check':
        if result.get('verdict') == 'execution_failed':
            return 'refine', 'repair'
        if result.get('verdict') == 'invalid_design':
            return 'design', 'redesign'
        if result.get('verdict') not in ('supported', 'refuted', 'inconclusive'):
            return 'blocked', None
    if stage == 'decision':
        decision = result.get('decision')
        if decision not in ('proceed', 'pivot', 'refine', 'abort'):
            return 'blocked', None
        # A paper-oriented native decision must not override failed/insufficient evidence.
        if decision == 'proceed' and current['result_check']['verdict'] != 'supported':
            return 'blocked', None
        return 'archive', None
    if stage == 'archive':
        decision = current['decision']['decision']
        if decision in ('proceed', 'abort'):
            return ('ready_for_formal_review' if decision == 'proceed' else 'stopped'), None
        return rollbacks[decision], decision
    if stage == 'refine':
        return 'execute', None
    return ORDER[ORDER.index(stage) + 1], None


def validate(config):
    from .loop import validate as validate_limits
    limits = dict(config, stages={s: {'command': ['validation-only']} for s in
                                 ('generate', 'debate', 'minimum_check', 'revise', 'archive')})
    validate_limits(limits)
    for stage in REQUIRED:
        spec = config.get('stages', {}).get(stage, {})
        if (('command' in spec) + ('job' in spec)) != 1:
            raise ValueError(f'{stage}: supply one native job or command hook')
        if 'command' in spec and (not isinstance(spec['command'], list) or not spec['command'] or
                                 any(not isinstance(x, str) or not x for x in spec['command'])):
            raise ValueError(f'{stage}: worker is not configured')


def run_claw_workflow(root, config, resume=None, retry=False, executor=execute):
    if os.name != 'posix':
        raise RuntimeError('Use WSL/Linux/macOS')
    import fcntl
    validate(config)
    root = Path(root).resolve()
    env_path = root / '.environments' / 'claw' / 'ready.json'
    prepared = json.loads(env_path.read_text()) if env_path.exists() else {}
    source = verify(root, 'claw', config.get('source') or prepared.get('source'))
    sys.path.insert(0, str(source))
    from researchclaw.pipeline.stages import Stage, DECISION_ROLLBACK
    names = {Stage.HYPOTHESIS_GEN: 'generate', Stage.ITERATIVE_REFINE: 'refine'}
    rollbacks = {k: names[v] for k, v in DECISION_ROLLBACK.items()}
    digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    folder = Path(resume).resolve() if resume else root / 'runs' / ('claw_' + uuid.uuid4().hex)
    folder.mkdir(parents=True, exist_ok=True)
    state_path = folder / 'state.json'
    with (folder / 'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if resume:
            state = json.loads(state_path.read_text())
            if state['config_sha256'] != digest:
                raise ValueError('Resume requires the same saved config')
            if state['status'] not in ('ready', 'running', 'blocked', 'awaiting_human'):
                return state
            if state['status'] == 'running':
                state['active_seconds'] += state.pop('reservation', 0)
                state.update(status='blocked', reason='Interrupted invocation; inspect side effects before retry')
                save(state_path, state)
            if state['status'] == 'blocked' and (not retry or state.get('scientific_blocker')):
                return state
        else:
            state = dict(config_sha256=digest, output=str(folder), status='ready', stage='generate',
                         round=1, calls=0, active_seconds=0, current={}, history=[], feedback={})
            save(folder / 'config.json', config)
        if state['status'] == 'awaiting_human':
            stage = state['stage']
            attempt = Path(state['attempt'])
            review_path = attempt / 'human-review.json'
            if not review_path.exists():
                return state
            raw = state['current'][stage]
            review = json.loads(review_path.read_text())
            if review['report_sha256'] != report_digest(raw) or review['config_sha256'] != digest:
                raise ValueError('Human review does not match this report/configuration')
            result = dict(raw, human_review=review)
            nxt, kind = route(stage, result, state['current'], rollbacks)
            if advance_result(state, folder, state_path, stage, result, attempt, nxt, kind):
                return state
        while True:
            if state['round'] > config['max_rounds'] or state['calls'] >= config['max_calls'] or state['active_seconds'] >= config['max_seconds']:
                state.update(status='budget_exhausted', reason='Budget reached; no forced proceed')
                save(state_path, state)
                return state
            stage = state['stage']
            attempt = folder / f"{state['calls'] + 1:04d}_{stage}"
            attempt.mkdir()
            context = dict(input=config.get('input', {}), current=state['current'], feedback=state['feedback'],
                           history=state['history'], round=state['round'], stage=stage, root=str(root),
                           workspace=str(folder / 'native'), output=str(attempt))
            timeout = min(config['stage_timeout'], config['max_seconds'] - state['active_seconds'])
            state.update(status='running', attempt=str(attempt), reservation=timeout)
            state['calls'] += 1
            save(state_path, state)
            save(attempt / 'context.json', context)
            start = time.monotonic()
            try:
                result = executor(root, config['stages'][stage], context, attempt, timeout)
                if not isinstance(result, dict):
                    raise ValueError('Expected result object')
                if 'human_review' in result:
                    raise ValueError('Worker cannot supply human approval')
                if 'status' in result and result['status'] != 'done':
                    raise RuntimeError('Native stage not completed: ' + result['status'])
                if stage == 'result_check':
                    verdict = result.get('verdict')
                    checked = dict(result, verdict=verdict if verdict in ('supported', 'refuted', 'inconclusive') else 'inconclusive')
                    checked = check_result('minimum_check', checked, root)
                    result = dict(checked, verdict=verdict)
                nxt, feedback_kind = route(stage, result, state['current'], rollbacks)
                if stage == 'discuss_select':
                    native_dir = folder / 'native' / 'stage-08'
                    native_dir.mkdir(parents=True, exist_ok=True)
                    (native_dir / 'hypotheses.md').write_text(result['selected']['text'], encoding='utf-8')
                    save(native_dir / 'selection.json', result)
                save(attempt / 'validated-result.json', result)
            except Exception as exc:
                state['active_seconds'] += time.monotonic() - start
                state.pop('reservation', None)
                state.update(status='blocked', scientific_blocker=False, reason=f'{stage}: {exc}')
                save(state_path, state)
                return state
            state['active_seconds'] += time.monotonic() - start
            state.pop('reservation', None)
            if advance_result(state, folder, state_path, stage, result, attempt, nxt, feedback_kind):
                return state


def advance_result(state, folder, state_path, stage, result, attempt, nxt, feedback_kind):
    state['current'][stage] = result
    state['history'].append({'stage': stage, 'result': result, 'attempt': str(attempt)})
    if nxt == 'awaiting_human':
        candidate = (state['current']['discuss_select']['selected'] if stage == 'novelty_selected'
                     else state['current']['generate'])
        save(attempt / 'review-request.json', dict(stage=stage, candidate=candidate,
             machine_report=result, decisions=['continue', 'differentiate', 'reject', 'need_evidence']))
    if nxt in ('blocked', 'stopped', 'ready_for_formal_review', 'awaiting_human'):
        state.update(status=nxt, scientific_blocker=nxt == 'blocked', reason=f'{stage}: {nxt}')
        save(state_path, state)
        return True
    if feedback_kind:
        # Preserve old native files outside Claw's artifact search before redesign/pivot.
        if nxt in ('generate', 'design'):
            import shutil
            cutoff = 8 if nxt == 'generate' else 9
            snapshot = folder / 'snapshots' / f"rollback_{state['calls']:04d}"
            for old_stage in (folder / 'native').glob('stage-*'):
                suffix = old_stage.name.removeprefix('stage-')
                if suffix.isdigit() and int(suffix) >= cutoff:
                    snapshot.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_stage), str(snapshot / old_stage.name))
        state['feedback'] = {'kind': feedback_kind, 'source_stage': stage, 'results': dict(state['current'])}
        # Keep immutable attempt artifacts; remove stale downstream values from active context.
        invalidated = ORDER[ORDER.index(nxt):] if nxt in ORDER else ORDER[ORDER.index('execute'):]
        for name in invalidated:
            state['current'].pop(name, None)
        state['current'].pop('refine', None)
        state['round'] += 1
    state.update(status='ready', stage=nxt, scientific_blocker=False)
    save(state_path, state)

    return False


def report_digest(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()


def record_novelty_review(folder, decision, reason, reviewer):
    """Record an explicit human decision; no model is called and no approval is inferred."""
    if decision not in ('continue', 'differentiate', 'reject', 'need_evidence'):
        raise ValueError('Unknown novelty decision')
    if not reason.strip() or not reviewer.strip():
        raise ValueError('Reviewer and reason are required')
    import fcntl
    folder = Path(folder).resolve()
    with (folder / 'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads((folder / 'state.json').read_text())
        if state['status'] != 'awaiting_human':
            raise ValueError('This run is not waiting for a novelty decision')
        record = dict(decision=decision, reason=reason, reviewer=reviewer, recorded_at=time.time(),
                      stage=state['stage'], config_sha256=state['config_sha256'],
                      report_sha256=report_digest(state['current'][state['stage']]))
        path = Path(state['attempt']) / 'human-review.json'
        with path.open('x', encoding='utf-8') as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
        return record
