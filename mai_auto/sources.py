"""Pinned source management. No patches, monkeypatches, or automatic upgrades."""
import json
from pathlib import Path
import subprocess


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def lock(root):
    return json.loads((Path(root) / 'upstreams.lock.json').read_text())['repositories']


def verify(root, key, path=None):
    entry = lock(root)[key]
    path = Path(path or Path(root) / '.vendor' / key).resolve()
    if not (path / '.git').exists():
        raise RuntimeError(f'{key}: checkout missing: {path}')
    if git(path, 'rev-parse', 'HEAD') != entry['sha']:
        raise RuntimeError(f'{key}: HEAD differs from lock')
    if git(path, 'status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError(f'{key}: source checkout is modified; use a clean pinned checkout')
    return path


def bootstrap(root, keys):
    for key in keys:
        entry = lock(root)[key]
        path = Path(root).resolve() / '.vendor' / key
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout', entry['url'], str(path)], check=True)
            subprocess.run(['git', '-C', str(path), 'checkout', '--detach', entry['sha']], check=True)
        verify(root, key, path)
