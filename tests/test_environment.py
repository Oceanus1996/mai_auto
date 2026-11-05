import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from mai_auto.environment import check_environment
from mai_auto.runner import run

ROOT = Path(__file__).resolve().parents[1]


class EnvironmentTests(unittest.TestCase):
    def test_missing_source_returns_setup_request(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            result = check_environment(ROOT, 'claw', 'claw_debate', {'source': str(output / 'missing')}, output)
            self.assertEqual(result['status'], 'needs_environment')
            self.assertTrue((output / 'environment-request.json').exists())
            self.assertIn('checkout missing', result['reason'])

    def test_stale_descriptor_not_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'upstreams.lock.json').write_bytes((ROOT / 'upstreams.lock.json').read_bytes())
            profile = root / '.environments/claw'
            profile.mkdir(parents=True)
            (profile / 'ready.json').write_text(json.dumps({'source_commit': 'old', 'python': sys.executable}))
            result = check_environment(root, 'claw', 'claw_debate', {}, root)
            self.assertEqual(result['status'], 'needs_environment')
            self.assertIn('different source revision', result['reason'])

    @unittest.skipUnless(os.environ.get('MAI_TEST_SETUP_CLAW'), 'requires agent-prepared environment')
    def test_runner_reuses_prepared_environment(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                raw = json.dumps({'choices': [{'message': {'content': 'SCRIPTED ENVIRONMENT TEST ONLY'}}]}).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            record = run(ROOT, {'adapter': 'claw_debate', 'agent_id': 'setup-smoke', 'timeout': 30,
                'model': {'base_url': f'http://127.0.0.1:{server.server_port}/v1', 'model': 'scripted-test'},
                'input': {'variables': {'topic': 'fixture', 'synthesis': 'fixture'}, 'rounds': 1}})
            self.assertEqual(record['status'], 'completed', record)
            evidence = json.loads((ROOT / 'runs' / record['run_id'] / 'environment.json').read_text())
            prepared = json.loads((ROOT / '.environments/claw/ready.json').read_text())
            self.assertEqual(evidence['python'], prepared['python'])
            self.assertEqual(evidence['model_ready'], 'not_checked')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
