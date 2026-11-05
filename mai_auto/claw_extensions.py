"""Protocol adapters around pinned Claw algorithms; no replacement research prompts."""
import hashlib
import json
from pathlib import Path


def discuss_select(payload, output, llm, prompts, debate, parse_winner):
    candidates = payload['candidates']
    if not candidates or len(candidates) > payload.get('max_candidates', 4):
        raise ValueError('Provide 1..max_candidates candidates')
    ids = [c['id'] for c in candidates]
    if len(set(ids)) != len(ids) or any(not c.get('text', '').strip() for c in candidates):
        raise ValueError('Candidates require unique IDs and nonempty original text')
    revisions = []
    for index, candidate in enumerate(candidates):
        # Candidate is input evidence in the existing synthesis variable, not a new prompt.
        variables = {'topic': payload['topic'], 'synthesis': json.dumps({
            'literature_synthesis': payload['synthesis'], 'candidate': candidate,
            'feedback': payload.get('feedback', {})}, ensure_ascii=False)}
        text, record = debate(panel=[llm], judge=llm, roles=prompts.debate_roles_hypothesis(),
            variables=variables, rounds=payload.get('rounds', 1), synth_prompt='hypothesis_synthesize',
            out_dir=output / f'candidate_{index}', prompts=prompts,
            author_model=llm.config.primary_model)
        # Native debate can return concatenated perspectives on judge failure.
        # It must not be represented as an independently validated conclusion.
        digest = hashlib.sha256(text.encode()).hexdigest()
        revisions.append({'id': f"{candidate['id']}@{digest[:16]}", 'parent_id': candidate['id'],
                          'text': text, 'sha256': digest, 'debate_record': record})
    (output / 'revisions.json').write_text(json.dumps(revisions, ensure_ascii=False, indent=2))
    combined = '\n\n---\n\n'.join(f"### Candidate {i}\n{c['text']}" for i, c in enumerate(revisions))
    prompt = prompts.sub_prompt('tournament_rank', n=len(revisions), candidates=combined)
    kwargs = {'system': prompt.system}
    if prompt.max_tokens:
        kwargs['max_tokens'] = prompt.max_tokens
    raw = llm.chat([{'role': 'user', 'content': prompt.user}], **kwargs).content
    (output / 'judge_verdict.md').write_text(raw)
    winner, scores = parse_winner(raw, len(revisions))
    if winner is None:
        raise ValueError('No parseable selection; do not silently choose candidate 0')
    return {'selected': revisions[winner], 'revisions': revisions, 'scores': scores,
            'model_independence': False, 'scientific_verdict': 'not_assessed',
            'adaptation': 'native per-candidate debate then native ranking prompt/parser; no regeneration'}


def novelty(payload):
    from researchclaw.literature.novelty import check_novelty
    report = check_novelty(topic=payload['topic'], hypotheses_text=payload['text'],
                           papers_already_seen=payload.get('papers', []))
    # Keyword similarity is screening evidence, not a proof of originality.
    return {'report': report, 'claim_sha256': hashlib.sha256(payload['text'].encode()).hexdigest(),
            'scientific_verdict': 'not_assessed'}


def native_stage(payload, output):
    """Call Claw's stage executor with its own config, dependencies and model client."""
    from dataclasses import asdict
    from researchclaw.config import RCConfig
    from researchclaw.adapters import AdapterBundle
    from researchclaw.pipeline.executor import execute_stage
    from researchclaw.pipeline.stages import Stage
    from researchclaw.llm.client import LLMClient
    config = RCConfig.load(payload['config'])
    stage = Stage(payload['stage'])
    if not 1 <= int(stage) <= 15:
        raise ValueError('This research driver stops before paper generation/publication')
    if config.experiment.mode == 'simulated':
        raise ValueError('Simulated mode cannot be used as real research evidence')
    if config.openclaw_bridge.use_message or config.openclaw_bridge.use_sessions_spawn:
        raise ValueError('Disable messaging and external session spawning for this bridge')
    # Prevent executor silently using its deterministic fallback for absent credentials.
    client = LLMClient.from_rc_config(config)
    if not client.config.base_url or not client.config.api_key:
        raise ValueError('Native Claw model configuration is missing')
    workspace = Path(payload['workspace']).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    result = execute_stage(stage, run_dir=workspace, run_id=payload.get('run_id', workspace.name),
        config=config, adapters=AdapterBundle.from_config(config),
        auto_approve_gates=payload.get('auto_approve_gates', False))
    import shutil
    stage_dir = workspace / f'stage-{int(stage):02d}'
    if stage_dir.exists():
        shutil.copytree(stage_dir, Path(output) / 'native-stage', symlinks=True)
    return dict(asdict(result), artifact_snapshot=str(Path(output) / 'native-stage'))
