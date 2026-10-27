#!/usr/bin/env python3
"""Stage upstream changes for OpenCode review, then apply a reviewed candidate."""
import argparse
import hashlib
import io
import json
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '.pstack', 'node_modules', '__pycache__'}
POINTER = 'Read [OpenCode runtime contract](../opencode-runtime.md) before executing this skill. It governs tools, models, settings, history, delegation, and authorization in all referenced files.\n'


def command(*args, cwd=None):
    try:
        return subprocess.run(args, cwd=cwd, check=True, capture_output=True).stdout
    except subprocess.CalledProcessError as error:
        details = (error.stderr or error.stdout or b'').decode(errors='replace').strip()
        raise ValueError(f'Command {args!r} failed (exit {error.returncode}): {details or "no diagnostic output"}') from error


def safe_path(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or '..' in path.parts or '\\' in name or path.as_posix() != name:
        raise ValueError(f'Unsafe path: {name!r}')
    return path


def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f'Symlink is not supported: {path}')
        if path.is_file():
            result[relative.as_posix()] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        elif not path.is_dir():
            raise ValueError(f'Non-regular path: {path}')
    return result


def installed_dependency_paths(root):
    found = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except FileNotFoundError:
            continue
        for child in children:
            if child.is_symlink() or not child.is_dir():
                continue
            if child.name in EXCLUDED:
                if child.name == 'node_modules':
                    found.append(child.relative_to(root).as_posix())
                continue
            stack.append(child)
    return sorted(found)


def reject_installed_dependencies(root):
    found = installed_dependency_paths(root)
    if found:
        raise ValueError('Installed dependencies are not allowed in the candidate: ' + ', '.join(found))


def snapshot(tree):
    return {name: {'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode}
            for name, (data, mode) in tree.items()}


def archive(source, ref):
    if source:
        sha = command('git', 'rev-parse', '--verify', f'{ref}^{{commit}}', cwd=source).decode().strip()
        raw = command('git', 'archive', f'{sha}:pstack', cwd=source)
    else:
        sha = json.loads(command('gh', 'api', f'repos/cursor/plugins/commits/{ref}'))['sha']
        raw = command('gh', 'api', f'repos/cursor/plugins/tarball/{sha}')
    if not re.fullmatch(r'[a-f0-9]{40}', sha):
        raise ValueError('Upstream did not resolve to an immutable commit')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for member in tar:
            name = member.name.rstrip('/')
            safe_path(name)
            if not source:
                parts = PurePosixPath(name).parts
                if len(parts) < 2 or parts[1] != 'pstack':
                    continue
                name = '/'.join(parts[2:])
                if not name:
                    continue
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f'Non-regular archive entry: {member.name}')
            if name in result:
                raise ValueError(f'Duplicate archive entry: {name}')
            result[name] = (tar.extractfile(member).read(), 0o755 if member.mode & 0o111 else 0o644)
    return sha, result


def mapped(tree):
    output, ignored = {}, []
    for name, entry in tree.items():
        if name.startswith(('skills/', 'agents/', 'assets/')) or name == 'LICENSE':
            target = name
        elif name == 'README.md':
            target = 'docs/upstream/README.md'
        elif name.startswith('docs/guide/'):
            target = 'docs/upstream/guide/' + name[len('docs/guide/'):]
        else:
            ignored.append(name)
            continue
        output[target] = entry
    return output, sorted(ignored)


def write_tree(root, tree):
    for name, (data, mode) in tree.items():
        safe_path(name)
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(mode)


def merge(old, local, incoming):
    if local == old or local == incoming:
        return incoming, None
    if incoming == old:
        return local, None
    if old is None or local is None or incoming is None:
        return local, 'addition/deletion'
    if b'\0' in old[0] + local[0] + incoming[0]:
        return local, 'binary'
    mode = incoming[1] if local[1] == old[1] else local[1]
    if local[1] != old[1] and incoming[1] != old[1] and local[1] != incoming[1]:
        return local, 'mode'
    with tempfile.TemporaryDirectory(prefix='pstack-merge-') as directory:
        paths = [Path(directory) / name for name in ('local', 'base', 'upstream')]
        for path, entry in zip(paths, (local, old, incoming)):
            path.write_bytes(entry[0])
        merged = subprocess.run(['git', 'merge-file', '-p', '-L', 'opencode', '-L', 'baseline', '-L', 'upstream', *map(str, paths)], capture_output=True)
        if not 0 <= merged.returncode <= 127:
            return local, 'binary or merge failure'
        return (merged.stdout, mode), 'text' if merged.returncode else None


def prepare(root, stage, source, ref):
    if any(path.is_symlink() for path in (stage, *stage.parents)):
        raise ValueError('Stage path must not pass through a symlink')
    if stage == root or root.is_relative_to(stage):
        raise ValueError('Stage must not contain the source root')
    if stage.is_relative_to(root) and stage.relative_to(root).parts[0] != '.pstack':
        raise ValueError('Stages inside the source root must use .pstack/')
    if stage.exists() or stage.is_symlink():
        raise ValueError(f'Stage already exists: {stage}')
    initial = files(root)
    metadata = json.loads(initial['docs/UPSTREAM.json'][0])
    baseline, old_raw = archive(source, metadata['commit'])
    target, new_raw = archive(source, ref)
    old, _ = mapped(old_raw)
    new, ignored = mapped(new_raw)
    candidate = dict(initial)
    changes, conflicts = [], []
    for name in sorted(old.keys() | new.keys()):
        if old.get(name) == new.get(name):
            continue
        entry, conflict = merge(old.get(name), initial.get(name), new.get(name))
        if name not in old and entry and name.endswith('/SKILL.md'):
            text = entry[0].decode()
            if '../opencode-runtime.md' not in text:
                parts = text.split('---', 2)
                if len(parts) != 3 or parts[0]:
                    raise ValueError(f'New skill lacks frontmatter: {name}')
                text = '---' + parts[1] + '---\n' + POINTER + parts[2]
                entry = (text.encode(), entry[1])
        if entry is None:
            candidate.pop(name, None)
        else:
            candidate[name] = entry
        changes.append(name)
        if conflict:
            conflicts.append({'path': name, 'kind': conflict})
    structural = set()
    for name in candidate:
        for parent in PurePosixPath(name).parents:
            if parent.as_posix() in candidate:
                structural.add(parent.as_posix())
    for name in sorted(structural, key=lambda item: (len(PurePosixPath(item).parts), item)):
        if any(name.startswith(parent + '/') for parent in structural):
            continue
        for child in list(candidate):
            if child == name or child.startswith(name + '/'):
                del candidate[child]
        candidate.update({child: entry for child, entry in initial.items()
                          if child == name or child.startswith(name + '/')})
        conflicts = [item for item in conflicts
                     if item['path'] != name and not item['path'].startswith(name + '/')]
        conflicts.append({'path': name, 'kind': 'file/directory'})
    if changes:
        metadata['commit'] = target
        for name in ('.cursor-plugin/plugin.json', '.claude-plugin/plugin.json', 'plugin.json'):
            if name in new_raw:
                version = json.loads(new_raw[name][0]).get('version')
                if version:
                    metadata['version'] = version
                    break
        candidate['docs/UPSTREAM.json'] = ((json.dumps(metadata, indent=2) + '\n').encode(), initial['docs/UPSTREAM.json'][1])
    plan = {'schema': 1, 'baseline': baseline, 'target': target, 'initial': snapshot(initial),
            'changes': changes, 'conflicts': conflicts, 'ignored': ignored,
            'status': 'needs-resolution' if conflicts else 'needs-review', 'tree': 'tree'}
    stage.mkdir(parents=True)
    write_tree(stage / 'tree', candidate)
    for conflict in conflicts:
        name = conflict['path']
        for label, tree in (('baseline', old), ('upstream', new)):
            write_tree(stage / 'conflicts' / label,
                       {child: entry for child, entry in tree.items()
                        if child == name or child.startswith(name + '/')})
    (stage / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(f'Staged {len(changes)} upstream changes with {len(conflicts)} conflicts at {stage}')
    if changes:
        print('Review candidate, resolve conflicts, clear plan.json conflicts, then apply --reviewed.')
    else:
        print('No upstream pstack content changes; working files and metadata remain unchanged.')


def apply(root, stage, reviewed):
    if not reviewed:
        raise ValueError('Apply requires --reviewed after OpenCode compatibility review')
    if any(path.is_symlink() for path in (stage, *stage.parents)):
        raise ValueError('Stage path must not pass through a symlink')
    for path in stage.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Stage contains symlink: {path}')
    plan = json.loads((stage / 'plan.json').read_text())
    if plan.get('schema') != 1 or plan.get('tree') != 'tree':
        raise ValueError('Unsupported sync plan')
    for name in plan['initial']:
        safe_path(name)
    if plan['conflicts']:
        raise ValueError('Resolve conflicts and clear plan.json conflicts before applying')
    current = files(root)
    if snapshot(current) != plan['initial']:
        raise ValueError('Local files changed since preparation; prepare a fresh stage')
    reject_installed_dependencies(stage / 'tree')
    candidate = files(stage / 'tree')
    if 'docs/UPSTREAM.json' not in candidate:
        raise ValueError('Candidate lacks upstream metadata')
    metadata = json.loads(candidate['docs/UPSTREAM.json'][0])
    expected_commit = plan['target'] if plan['changes'] else plan['baseline']
    if metadata.get('commit') != expected_commit:
        raise ValueError('Candidate upstream commit does not match the sync plan')
    for name, (data, _) in candidate.items():
        if re.search(rb'^(<<<<<<< |=======\s*$|>>>>>>> )', data, re.MULTILINE):
            raise ValueError(f'Unresolved conflict markers: {name}')
    subprocess.run([sys.executable, str(root / 'scripts/check-plugin.py'), '--root', str(stage / 'tree')], check=True)
    if snapshot(files(root)) != plan['initial']:
        raise ValueError('Local files changed during validation')
    changed = sorted(name for name in current.keys() | candidate.keys() if current.get(name) != candidate.get(name))
    changed.sort(key=lambda name: name == 'docs/UPSTREAM.json')
    removed = set(current) - set(candidate)
    for name in candidate:
        target = root / name
        for parent in target.parents:
            if parent == root:
                break
            relative = parent.relative_to(root).as_posix()
            if parent.is_symlink() or (parent.exists() and not parent.is_dir() and relative not in removed):
                raise ValueError(f'Path layout conflict: {relative}')
        if target.is_dir():
            for occupant in target.rglob('*'):
                relative = occupant.relative_to(root)
                if (occupant.is_symlink() or any(part in EXCLUDED for part in relative.parts)
                        or (not occupant.is_dir() and relative.as_posix() not in removed)):
                    raise ValueError(f'Path layout conflict: {relative}')

    def prune(parent):
        while parent != root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    original_directories = {path: stat.S_IMODE(path.stat().st_mode) for path in root.rglob('*')
                            if path.is_dir() and not path.is_symlink()
                            and not any(part in EXCLUDED for part in path.relative_to(root).parts)}
    try:
        for name in changed:
            if name not in candidate:
                path = root / name
                path.unlink()
                prune(path.parent)
        for name in changed:
            if name in candidate:
                target = root / name
                if target.is_dir():
                    for directory in sorted(target.rglob('*'), key=lambda path: len(path.parts), reverse=True):
                        directory.rmdir()
                    target.rmdir()
                write_tree(root, {name: candidate[name]})
    except OSError:
        for name in sorted(changed, key=lambda item: len(PurePosixPath(item).parts), reverse=True):
            path = root / name
            if path.is_file():
                path.unlink()
                prune(path.parent)
        for path in sorted(root.rglob('*'), key=lambda item: len(item.parts), reverse=True):
            if (path.is_dir() and path not in original_directories
                    and not any(part in EXCLUDED for part in path.relative_to(root).parts)
                    and not any(path.iterdir())):
                path.rmdir()
        for path, mode in original_directories.items():
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(mode)
        for name in changed:
            if name in current:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(current[name][0])
                path.chmod(current[name][1])
        raise
    print(f'Applied {len(changed)} reviewed files from {plan["target"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('prepare', 'apply'), default='prepare')
    parser.add_argument('--ref', default='main')
    parser.add_argument('--source', type=Path, help='Local cursor/plugins git checkout for offline use')
    parser.add_argument('--stage', type=Path, default=Path('.pstack/upstream-sync'))
    parser.add_argument('--reviewed', action='store_true')
    args = parser.parse_args()
    stage = args.stage.absolute()
    try:
        if args.action == 'prepare':
            prepare(ROOT, stage, args.source, args.ref)
        else:
            apply(ROOT, stage, args.reviewed)
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError, tarfile.TarError) as error:
        parser.exit(1, f'sync-upstream: {error}\n')


if __name__ == '__main__':
    main()
