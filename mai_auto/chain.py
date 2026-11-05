"""Evidence storage only; no new literature retrieval or evolution inference algorithm."""
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid


class ChainStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS papers(id TEXT PRIMARY KEY, metadata TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS links(id TEXT PRIMARY KEY, source TEXT REFERENCES papers(id),
            target TEXT REFERENCES papers(id), kind TEXT NOT NULL, evidence TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY, content TEXT NOT NULL);
        ''')

    def add_paper(self, paper_id, metadata):
        with self.db:
            self.db.execute('INSERT INTO papers VALUES (?,?)', (paper_id, json.dumps(metadata, sort_keys=True)))

    def link(self, source, target, kind, evidence):
        if kind not in ('citation', 'evolution'):
            raise ValueError('Unknown link kind')
        if not isinstance(evidence, dict) or not evidence.get('locator') or evidence.get('status') not in ('supported', 'inference', 'unknown'):
            raise ValueError('Require locator and explicit evidence status')
        if source == target:
            raise ValueError('Self links are not allowed')
        link_id = uuid.uuid4().hex
        with self.db:
            self.db.execute('INSERT INTO links VALUES (?,?,?,?,?)',
                            (link_id, source, target, kind, json.dumps(evidence, sort_keys=True)))
        return link_id

    def snapshot(self):
        # One read transaction prevents a mixed snapshot under concurrent updates.
        with self.db:
            self.db.execute('BEGIN')
            content = json.dumps({table: self.db.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()
                                  for table in ('papers', 'links')}, sort_keys=True)
            digest = hashlib.sha256(content.encode()).hexdigest()
            self.db.execute('INSERT OR IGNORE INTO snapshots VALUES (?,?)', (digest, content))
        return digest

    def close(self):
        self.db.close()
