"""Routing tests: deterministic fixtures, never scientific findings."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from mai_auto.claw_workflow import REQUIRED, route, run_claw_workflow, record_novelty_review


class Routing(unittest.TestCase):
    def test_proceed_requires_positive_evidence(self):
        self.assertEqual(route('decision', {'decision': 'proceed'},
            {'result_check': {'verdict': 'refuted'}}, {})[0], 'blocked')

    def test_novelty_machine_cannot_approve(self):
        result = {'report': {'recommendation': 'proceed'},
                  'claim_sha256': hashlib.sha256(b'claim').hexdigest()}
        self.assertEqual(route('novelty', result, {'generate': {'text': 'claim'}}, {}), ('awaiting_human', None))

    def test_revision_requires_own_novelty_report(self):
        with self.assertRaises(ValueError):
            route('novelty_selected', {'report': {}, 'claim_sha256': 'old'},
                  {'discuss_select': {'selected': {'text': 'new'}}}, {})

    def test_failures_go_to_distinct_stages(self):
        for verdict, target in [('execution_failed', 'refine'), ('invalid_design', 'design'), ('refuted', 'analyze')]:
            self.assertEqual(route('result_check', {'verdict': verdict}, {}, {})[0], target)


@unittest.skipUnless(os.environ.get('MAI_TEST_CLAW'), 'requires pinned Claw checkout')
class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        project = Path(__file__).resolve().parents[1]
        (self.root / 'upstreams.lock.json').write_bytes((project / 'upstreams.lock.json').read_bytes())
        (self.root / 'evidence.txt').write_text('TEST FIXTURE ONLY')
        self.config = dict(source=os.environ['MAI_TEST_CLAW'], max_rounds=3, max_calls=40,
            max_seconds=30, stage_timeout=3, stages={s: {'command': ['fixture']} for s in REQUIRED})
        self.seen = []

    def worker(self, root, spec, ctx, output, timeout):
        stage = ctx['stage']
        self.seen.append(stage)
        if stage == 'generate':
            return {'text': 'new claim', 'candidates': [{'id': 'A', 'text': 'new claim'}]}
        if stage.startswith('novelty'):
            return {'claim_sha256': hashlib.sha256(b'new claim').hexdigest(),
                    'report': {'recommendation': 'proceed', 'search_coverage': 'sufficient'}}
        if stage == 'discuss_select':
            return {'selected': {'id': 'A@revision', 'text': 'new claim'}}
        if stage == 'plan_check':
            return {'verdict': 'pass'}
        if stage == 'result_check':
            return {'verdict': 'supported', 'evidence': ['evidence.txt']}
        if stage == 'decision':
            return {'decision': 'pivot' if ctx['round'] == 1 else 'proceed'}
        return {'text': 'fixture'}

    def drive(self, executor=None, resume=None, retry=False):
        worker = executor or self.worker
        state = run_claw_workflow(self.root, self.config, resume=resume, retry=retry, executor=worker)
        for _ in range(10):
            if state['status'] != 'awaiting_human':
                return state
            record_novelty_review(state['output'], 'continue', 'TEST FIXTURE APPROVAL', 'test reviewer')
            state = run_claw_workflow(self.root, self.config, resume=state['output'], executor=worker)
        self.fail('Too many fixture review gates')

    def test_manual_gate_and_stale_review(self):
        state = run_claw_workflow(self.root, self.config, executor=self.worker)
        self.assertEqual(state['status'], 'awaiting_human')
        self.assertNotIn('discuss_select', self.seen)
        calls = state['calls']
        state = run_claw_workflow(self.root, self.config, resume=state['output'], retry=True, executor=self.worker)
        self.assertEqual(state['calls'], calls)
        record_novelty_review(state['output'], 'continue', 'TEST FIXTURE', 'reviewer')
        path = Path(state['output']) / 'state.json'
        state['current']['novelty']['report']['changed'] = True
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError, 'does not match'):
            run_claw_workflow(self.root, self.config, resume=state['output'], executor=self.worker)

    def test_worker_cannot_fake_human(self):
        def fake(root, spec, ctx, output, timeout):
            result = self.worker(root, spec, ctx, output, timeout)
            if ctx['stage'] == 'novelty':
                result['human_review'] = {'decision': 'continue'}
            return result
        state = run_claw_workflow(self.root, self.config, executor=fake)
        self.assertEqual(state['status'], 'blocked')
        self.assertIn('cannot supply human', state['reason'])

    def test_native_rollback_two_rounds(self):
        state = self.drive()
        self.assertEqual(state['status'], 'ready_for_formal_review')
        self.assertEqual(self.seen.count('generate'), 2)
        self.assertEqual(self.seen.count('archive'), 2)
        self.assertEqual(state['feedback']['kind'], 'pivot')
        self.assertEqual((Path(state['output']) / 'native/stage-08/hypotheses.md').read_text(), 'new claim')

    def test_redesign_skips_generation_and_resume_skips_completed(self):
        def worker(root, spec, ctx, output, timeout):
            if ctx['stage'] == 'plan_check' and ctx['round'] == 1:
                self.seen.append('plan_check')
                return {'verdict': 'revise'}
            if ctx['stage'] == 'execute':
                raise RuntimeError('fixture outage')
            return self.worker(root, spec, ctx, output, timeout)
        state = self.drive(executor=worker)
        self.assertEqual(state['status'], 'blocked')
        self.assertEqual(self.seen.count('generate'), 1)
        self.assertEqual(self.seen.count('design'), 2)
        state = self.drive(resume=state['output'], retry=True)
        self.assertEqual(state['status'], 'ready_for_formal_review')
        self.assertEqual(self.seen.count('generate'), 1)

    def test_budget_never_forces_proceed(self):
        self.config['max_calls'] = 2
        state = self.drive()
        self.assertEqual(state['status'], 'budget_exhausted')
        self.assertNotIn('decision', self.seen)

    def test_evidence_required(self):
        def worker(root, spec, ctx, output, timeout):
            if ctx['stage'] == 'result_check':
                return {'verdict': 'supported', 'evidence': []}
            return self.worker(root, spec, ctx, output, timeout)
        state = self.drive(executor=worker)
        self.assertEqual(state['status'], 'blocked')
        self.assertNotIn('decision', self.seen)

    def test_missing_workers_fail_before_any_work(self):
        self.config['stages']['execute']['command'] = None
        with self.assertRaises(ValueError):
            run_claw_workflow(self.root, self.config, executor=self.worker)
        self.assertFalse(self.seen)

@unittest.skipUnless(os.environ.get('MAI_TEST_CLAW'), 'requires pinned Claw checkout')
class NativeDiscussion(unittest.TestCase):
    def test_native_debate_then_rank_and_reject_bad_verdict(self):
        import sys
        from types import SimpleNamespace
        sys.path.insert(0, os.environ['MAI_TEST_CLAW'])
        from researchclaw.prompts import PromptManager
        from researchclaw.pipeline.debate import run_debate
        from researchclaw.pipeline.tournament import _parse_winner
        from mai_auto.claw_extensions import discuss_select
        class ScriptedClient:
            config = SimpleNamespace(primary_model='fixture-only')
            def __init__(self, bad=False):
                self.calls = 0
                self.bad = bad
            def chat(self, *args, **kwargs):
                self.calls += 1
                return SimpleNamespace(content='INVALID' if self.bad else
                    '{"winner":1,"rankings":[{"id":0,"score":3},{"id":1,"score":5}]}')
        payload = {'topic': 'fixture', 'synthesis': 'fixture evidence', 'rounds': 1,
                   'candidates': [{'id': 'A', 'text': 'fixture A'}, {'id': 'B', 'text': 'fixture B'}]}
        prompts = PromptManager()
        with tempfile.TemporaryDirectory() as temp:
            client = ScriptedClient()
            result = discuss_select(payload, Path(temp), client, prompts, run_debate, _parse_winner)
            self.assertEqual(result['selected']['parent_id'], 'B')
            self.assertEqual(client.calls, 2 * (2 * len(prompts.debate_roles_hypothesis()) + 1) + 1)
            self.assertFalse(result['model_independence'])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'No parseable selection'):
                discuss_select(payload, Path(temp), ScriptedClient(True), prompts, run_debate, _parse_winner)
