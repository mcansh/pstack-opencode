#!/usr/bin/env python3
"""Check and export the bounded upstream update used by GitHub Actions."""
import argparse
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_upstream', ROOT / 'scripts/sync-upstream.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def allowed(name):
    sync.safe_path(name)
    return name.startswith(('skills/', 'agents/', 'assets/', 'docs/upstream/')) or name in ('LICENSE', 'docs/UPSTREAM.json')


def has_changes(stage):
    return bool(json.loads((stage / 'plan.json').read_text())['changes'])


def verify(root, stage, original, applied=False):
    plan = json.loads((stage / 'plan.json').read_text())
    baseline = json.loads(original.read_text())
    for key in baseline.keys() | plan.keys():
        if key not in ('conflicts', 'status') and plan.get(key) != baseline.get(key):
            raise ValueError(f'Prepared plan field changed: {key}')
    if plan['conflicts']:
        raise ValueError('Unresolved upstream conflicts')
    if not applied:
        sync.reject_installed_dependencies(stage / 'tree')
    tree = sync.files(root if applied else stage / 'tree')
    current = sync.snapshot(tree)
    changed = sorted(name for name in current.keys() | baseline['initial'].keys()
                     if current.get(name) != baseline['initial'].get(name))
    for name in changed:
        if not allowed(name):
            raise ValueError(f'Change outside upstream scope: {name}')
        if name in tree and re.search(rb'^(<<<<<<< |=======\s*$|>>>>>>> )', tree[name][0], re.MULTILINE):
            raise ValueError(f'Unresolved conflict markers: {name}')
    if json.loads(tree['docs/UPSTREAM.json'][0]).get('commit') != baseline['target']:
        raise ValueError('Upstream provenance differs from prepared target')
    untracked = sync.command('git', 'ls-files', '--others', '-z', cwd=root).decode().split('\0')
    for name in filter(None, untracked):
        if any(part in sync.EXCLUDED for part in Path(name).parts):
            continue
        if name not in baseline['initial'] and not (applied and name in changed and allowed(name)):
            raise ValueError(f'Unexpected untracked source file: {name}')
    if not applied and sync.snapshot(sync.files(root)) != baseline['initial']:
        raise ValueError('Working source changed during adaptation')
    return changed


def export(root, stage, original, output):
    changed = verify(root, stage, original, applied=True)
    if not changed:
        raise ValueError('Reviewed sync produced no changes')
    additions = [name for name in changed if (root / name).is_file()]
    if additions:
        sync.command('git', 'add', '-N', '--', *additions, cwd=root)
    actual = set(filter(None, sync.command('git', 'diff', 'HEAD', '--name-only', '-z', cwd=root).decode().split('\0')))
    if actual != set(changed):
        raise ValueError('Git changes differ from the reviewed source snapshot')
    patch = sync.command('git', 'diff', 'HEAD', '--binary', '--full-index', '--', *changed, cwd=root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('detect', 'verify', 'apply', 'export'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--stage', type=Path, default=Path('.pstack/upstream-sync'))
    parser.add_argument('--original', type=Path, default=Path('.pstack/prepared-plan.json'))
    parser.add_argument('--output', type=Path, default=Path('.pstack/publication/upstream.patch'))
    args = parser.parse_args()
    try:
        if args.action == 'detect':
            value = str(has_changes(args.stage)).lower()
            print(f'has_changes={value}')
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                    output.write(f'has_changes={value}\n')
        elif args.action == 'verify':
            verify(args.root, args.stage, args.original)
        elif args.action == 'apply':
            verify(args.root, args.stage, args.original)
            sync.apply(args.root, args.stage, reviewed=True)
        else:
            export(args.root, args.stage, args.original, args.output)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'sync-action: {error}\n')


if __name__ == '__main__':
    main()
