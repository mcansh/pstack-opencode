#!/usr/bin/env python3
"""Validate the package and the audit's conservative worktree classification."""
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
ROOT = parser.parse_args().root.resolve()


def run(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True, capture_output=True).stdout


package = json.loads((ROOT / 'package.json').read_text())
assert package['name'] == 'pstack-opencode'
assert package['exports']['.'] == './index.js'
assert (ROOT / 'index.js').is_file()
assert (ROOT / 'skills/opencode-runtime.md').is_file()
assert not (ROOT / 'bin').exists()
assert not (ROOT / '.codex-plugin').exists()
assert 'Copyright (c) 2026 Lauren Tan' in (ROOT / 'LICENSE').read_text()
skills = sorted((ROOT / 'skills').glob('*/SKILL.md'))
repository_skills = sorted((ROOT / '.opencode/skills').glob('*/SKILL.md'))
assert skills
for path in [*skills, *repository_skills]:
    text = path.read_text()
    assert text.startswith('---\n'), path
    frontmatter = text.split('---', 2)[1]
    assert re.search(r'^name: ' + re.escape(path.parent.name) + r'$', frontmatter, re.MULTILINE), path
    assert re.search(r'^description: .+', frontmatter, re.MULTILINE), path
    assert re.search(r'^  opencode/autoinvoke: false$', frontmatter, re.MULTILINE), path
    if path in skills:
        assert '../opencode-runtime.md' in text, path
for path in (p for p in (ROOT / 'skills').rglob('*.md') if 'node_modules' not in p.parts):
    text = path.read_text()
    assert '.cursor/' not in text, path
    assert 'codex-runtime' not in text and 'codex-models' not in text, path
    assert 'disable-model-invocation:' not in text, path
    assert 'claude-opus-5-5-' not in text and 'grok-4.7-' not in text, path
for path in [ROOT / 'README.md', ROOT / 'docs/COMPATIBILITY.md', *repository_skills, *(p for p in (ROOT / 'skills').rglob('*.md') if 'node_modules' not in p.parts)]:
    for target in re.findall(r'\[[^\]\n]*\]\(([^)\s]+)\)', path.read_text()):
        if '://' in target or target.startswith(('#', '/', 'mailto:')) or '<' in target or target == 'url':
            continue
        target = target.split('#')[0]
        if target:
            assert (path.parent / target).exists(), f'{path.relative_to(ROOT)} -> {target}'

with tempfile.TemporaryDirectory(prefix='pstack-check-') as tmp:
    tmp = Path(tmp)
    repo = tmp / 'repo'
    run('git', 'init', '-q', '-b', 'main', str(repo))
    run('git', 'config', 'user.name', 'Package Check', cwd=repo)
    run('git', 'config', 'user.email', 'package-check@example.invalid', cwd=repo)
    run('git', 'config', 'commit.gpgsign', 'false', cwd=repo)
    (repo / 'tracked.txt').write_text('base\n')
    run('git', 'add', 'tracked.txt', cwd=repo)
    run('git', 'commit', '-qm', 'fixture', cwd=repo)
    worktree = tmp / 'worktree'
    run('git', 'worktree', 'add', '-q', '-b', 'candidate', str(worktree), cwd=repo)
    # No live forge calls: this fixture tests local classification only.
    bin_dir = tmp / 'bin'
    bin_dir.mkdir()
    for command in ('gh', 'origin'):
        stub = bin_dir / command
        stub.write_text('#!/bin/sh\nexit 1\n')
        stub.chmod(0o755)
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'])
    audit = Path(__file__).resolve().parents[1] / 'skills/poteto-mode/scripts/worktree-audit.sh'
    def row():
        output = run('bash', str(audit), '-b', 'main', str(repo), env=env)
        return next(line.split('\t') for line in output.splitlines() if line.endswith(str(worktree)))
    clean = row()
    assert clean[1] == '0d', clean
    assert clean[6:8] == ['unknown', 'verify-liveness'], clean
    (worktree / 'tracked.txt').write_text('uncommitted\n')
    dirty = row()
    assert dirty[3] == 'wip:1' and dirty[7] == 'hold-wip', dirty
    assert (worktree / 'tracked.txt').read_text() == 'uncommitted\n'
    (worktree / 'tracked.txt').write_text('base\n')
    (worktree / 'untracked.txt').write_text('keep me\n')
    untracked = row()
    assert untracked[3] == 'scratch:1' and untracked[7] != 'safe', untracked
    assert (worktree / 'untracked.txt').read_text() == 'keep me\n'
print(f'Package valid: {len(skills)} skills; worktree liveness, dirty, and untracked checks passed.')
