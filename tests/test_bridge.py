import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from mai_auto.chain import ChainStore
from mai_auto.transport import ModelTransport
from mai_auto.native import call
from mai_auto.sources import verify

ROOT = Path(__file__).resolve().parents[1]


class Contracts(unittest.TestCase):
    def test_skills_and_source_links(self):
        skills = list((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(skills), 15)
        for path in skills:
            content = path.read_text()
            self.assertTrue(content.startswith('---\nname: ' + path.parent.name))
            self.assertIn('description:', content)
            self.assertIn('upstreams.lock.json', content)
            self.assertNotIn('TODO', content)

    def test_transport_rejects_accidental_cloud(self):
        for url in ['https://example.com/v1', 'http://127.0.0.1.evil.test/v1', 'http://user:pass@localhost/v1']:
            with self.assertRaises(ValueError):
                ModelTransport(url, 'test')
        with self.assertRaises(ValueError):
            ModelTransport('http://example.com/v1', 'test', mode='api')
        with self.assertRaises(ValueError):
            ModelTransport('https://example.com/v1', 'test', mode='api')
        self.assertEqual(ModelTransport('http://127.0.0.1:8080/v1', 'test').config.primary_model, 'test')

    def test_chain_snapshots_and_integrity(self):
        with tempfile.TemporaryDirectory() as folder:
            db = ChainStore(Path(folder) / 'literature.sqlite')
            db.add_paper('P1', {'title': 'Example 1'})
            first = db.snapshot()
            self.assertEqual(first, db.snapshot())
            db.add_paper('P2', {'title': 'Example 2'})
            with self.assertRaises(ValueError):
                db.link('P1', 'P2', 'evolution', {})
            with self.assertRaises(sqlite3.IntegrityError):
                db.link('P1', 'missing', 'citation', {'locator': 'References', 'status': 'supported'})
            db.link('P1', 'P2', 'evolution', {'locator': 'Section 3', 'status': 'inference'})
            self.assertNotEqual(first, db.snapshot())
            self.assertEqual(len(db.db.execute('SELECT * FROM snapshots WHERE id=?', (first,)).fetchall()), 1)
            db.close()

    @unittest.skipUnless(os.environ.get('MAI_TEST_ARBOR'), 'set MAI_TEST_ARBOR to pinned Arbor checkout')
    def test_real_arbor_tree(self):
        source = verify(ROOT, 'arbor', os.environ['MAI_TEST_ARBOR'])
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            result = call('arbor_tree', source, {'topic': 'test', 'nodes': [
                {'id': 'A', 'parent_id': 'ROOT', 'hypothesis': 'first'},
                {'id': 'B', 'parent_id': 'A', 'hypothesis': 'second'}]}, output)
            self.assertEqual(result['nodes'][1]['children_ids'], ['B'])
            self.assertEqual(result['nodes'][2]['depth'], 2)
            self.assertTrue((output / 'idea_tree.md').exists())
            with self.assertRaises(ValueError):
                call('arbor_tree', source, {'topic': 'test', 'nodes': [
                    {'id': 'C', 'parent_id': 'missing', 'hypothesis': 'bad'}]}, output)
            restored = call('arbor_tree', source, {'topic': 'test'}, output)
            self.assertEqual(len(restored['nodes']), 3)

    def test_upstream_pin_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                verify(ROOT, 'arbor', folder)


if __name__ == '__main__':
    unittest.main()

class NativeDebate(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MAI_TEST_CLAW'), 'set MAI_TEST_CLAW to pinned AutoResearchClaw checkout')
    def test_native_rounds_with_scripted_transport_not_real_inference(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                data = json.dumps({'choices': [{'message': {'content': 'SCRIPTED_TEST_RESPONSE'}}]}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
            def log_message(self, *args):
                pass
        source = verify(ROOT, 'claw', os.environ['MAI_TEST_CLAW'])
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as folder:
                result = call('claw_debate', source,
                    {'variables': {'topic': 'test', 'synthesis': 'test evidence'}, 'rounds': 1},
                    Path(folder), {'base_url': f'http://127.0.0.1:{server.server_port}/v1', 'model': 'scripted-test'})
                self.assertFalse(result['record']['independent_judge'])
                roles = result['record']['roles']
                self.assertEqual(len(received), 2 * len(roles) + 1)
                self.assertTrue(all(r['messages'][0]['role'] == 'system' for r in received))
                for role in roles:
                    self.assertTrue((Path(folder) / 'debate' / f'{role}.r1.md').exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
