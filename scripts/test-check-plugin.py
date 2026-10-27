#!/usr/bin/env python3
"""Verify candidate validation never executes an incoming audit script."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='pstack-check-boundary-') as tmp:
    base = Path(tmp)
    candidate = base / 'candidate'
    shutil.copytree(root, candidate, ignore=shutil.ignore_patterns('.git', '.pstack', 'node_modules', '__pycache__'))
    marker = base / 'candidate-executed'
    (candidate / 'skills/poteto-mode/scripts/worktree-audit.sh').write_text('#!/bin/sh\nprintf touched > "$PSTACK_CANDIDATE_MARKER"\nexit 0\n')
    result = subprocess.run([sys.executable, str(root / 'scripts/check-plugin.py'), '--root', str(candidate)], capture_output=True, text=True, env=dict(os.environ, PSTACK_CANDIDATE_MARKER=str(marker)))
    assert not marker.exists(), 'Validation executed an incoming candidate script'
    assert result.returncode == 0, result.stderr
print('Candidate validation uses the trusted checkout audit script.')
