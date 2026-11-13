#!/usr/bin/env python3
"""Exercise sync using a local upstream and isolated OpenCode checkout."""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location('sync', Path(__file__).with_name('sync-upstream.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack-sync-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'upstream'
        self.root = self.base / 'opencode'
        self.stage = self.root / '.pstack/sync'
        self.source.mkdir()
        self.root.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'sync@example.invalid')
        self.git('config', 'user.name', 'Sync Test')
        self.git('config', 'commit.gpgsign', 'false')
        self.put('skills/example/SKILL.md', '---\nname: example\ndescription: Test\n---\n\nAlpha\n\nBeta\n\nGamma\n')
        self.put('skills/remove/file.md', 'remove\n')
        self.put('assets/binary', b'old\0image')
        self.put('.cursor-plugin/plugin.json', '{"version":"1.0.0"}')
        baseline = self.commit()
        for name, entry in sync.mapped(sync.archive(self.source, baseline)[1])[0].items():
            sync.write_tree(self.root, {name: entry})
        sync.write_tree(self.root, {'docs/UPSTREAM.json': ((json.dumps({'commit': baseline, 'version': '1.0.0'}) + '\n').encode(), 0o644)})
        self.write('scripts/check-plugin.py', 'import argparse\nfrom pathlib import Path\np=argparse.ArgumentParser()\np.add_argument("--root",required=True)\na=p.parse_args()\nassert (Path(a.root)/"docs/UPSTREAM.json").exists()\nassert not (Path(a.root)/"invalid").exists()\n')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.source, check=True, capture_output=True).stdout.decode().strip()

    def put(self, name, content):
        path = self.source / 'pstack' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def prepare(self):
        sync.prepare(self.root, self.stage, self.source, 'main')
        return json.loads((self.stage / 'plan.json').read_text())

    def test_preserves_opencode_and_applies_incoming_changes(self):
        path = 'skills/example/SKILL.md'
        self.write(path, (self.root / path).read_text().replace('Alpha', 'OpenCode Alpha'))
        self.put(path, (self.source / 'pstack' / path).read_text().replace('Gamma', 'Upstream Gamma'))
        self.put('skills/new/SKILL.md', '---\nname: new\ndescription: New\n---\nNew skill\n')
        self.put('agents/new.md', 'new agent\n')
        self.put('assets/run.sh', '#!/bin/sh\nexit 0\n')
        (self.source / 'pstack/assets/run.sh').chmod(0o755)
        (self.source / 'pstack/skills/remove/file.md').unlink()
        target = self.commit()
        before = sync.snapshot(sync.files(self.root))
        plan = self.prepare()
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))
        self.assertEqual([], plan['conflicts'])
        sync.apply(self.root, self.stage, True)
        result = (self.root / path).read_text()
        self.assertIn('OpenCode Alpha', result)
        self.assertIn('Upstream Gamma', result)
        self.assertIn('../opencode-runtime.md', (self.root / 'skills/new/SKILL.md').read_text())
        self.assertFalse((self.root / 'skills/remove/file.md').exists())
        self.assertTrue((self.root / 'agents/new.md').exists())
        self.assertEqual(0o755, (self.root / 'assets/run.sh').stat().st_mode & 0o777)
        self.assertIn('.cursor-plugin/plugin.json', plan['ignored'])
        self.assertEqual(target, json.loads((self.root / 'docs/UPSTREAM.json').read_text())['commit'])
        self.stage = self.root / '.pstack/second'
        self.assertEqual([], self.prepare()['changes'])
        before = sync.snapshot(sync.files(self.root))
        sync.apply(self.root, self.stage, True)
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))

    def test_no_content_changes_preserve_candidate_and_working_files(self):
        before = sync.snapshot(sync.files(self.root))
        for case in ('same revision', 'unrelated commit', 'ignored files'):
            with self.subTest(case=case):
                if case == 'unrelated commit':
                    (self.source / 'other-plugin.txt').write_text('unrelated change\n')
                    self.commit()
                elif case == 'ignored files':
                    self.put('.cursor-plugin/plugin.json', '{"version":"2.0.0"}')
                    self.put('docs/harness/claude-code.md', 'ignored instructions\n')
                    self.commit()
                self.stage = self.root / '.pstack' / case.replace(' ', '-')
                plan = self.prepare()
                self.assertEqual(self.git('rev-parse', 'HEAD'), plan['target'])
                self.assertEqual([], plan['changes'])
                self.assertEqual(before, sync.snapshot(sync.files(self.stage / 'tree')))
                sync.apply(self.root, self.stage, True)
                self.assertEqual(before, sync.snapshot(sync.files(self.root)))

    def test_text_conflict_and_review_gate(self):
        path = 'skills/example/SKILL.md'
        original = (self.root / path).read_text()
        self.write(path, original.replace('Beta', 'Local Beta'))
        self.put(path, original.replace('Beta', 'Incoming Beta'))
        self.commit()
        metadata = (self.root / 'docs/UPSTREAM.json').read_bytes()
        plan = self.prepare()
        self.assertEqual('text', plan['conflicts'][0]['kind'])
        self.assertIn('<<<<<<< opencode', (self.stage / 'tree' / path).read_text())
        with self.assertRaisesRegex(ValueError, '--reviewed'):
            sync.apply(self.root, self.stage, False)
        with self.assertRaisesRegex(ValueError, 'Resolve conflicts'):
            sync.apply(self.root, self.stage, True)
        plan['conflicts'] = []
        (self.stage / 'plan.json').write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, 'conflict markers'):
            sync.apply(self.root, self.stage, True)
        self.assertEqual(metadata, (self.root / 'docs/UPSTREAM.json').read_bytes())

    def test_binary_and_deletion_conflicts(self):
        (self.root / 'assets/binary').write_bytes(b'local\0image')
        self.write('skills/remove/file.md', 'local edit\n')
        self.put('assets/binary', b'incoming\0image')
        (self.source / 'pstack/skills/remove/file.md').unlink()
        self.commit()
        plan = self.prepare()
        self.assertEqual({'binary', 'addition/deletion'}, {item['kind'] for item in plan['conflicts']})
        self.assertEqual(b'incoming\0image', (self.stage / 'conflicts/upstream/assets/binary').read_bytes())
        self.assertEqual('local edit\n', (self.stage / 'tree/skills/remove/file.md').read_text())

    def test_drift_and_existing_stage_refused(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'Stage already exists'):
            self.prepare()
        metadata = (self.root / 'docs/UPSTREAM.json').read_bytes()
        self.write('new-collision', 'new local file')
        with self.assertRaisesRegex(ValueError, 'Local files changed'):
            sync.apply(self.root, self.stage, True)
        self.assertEqual(metadata, (self.root / 'docs/UPSTREAM.json').read_bytes())

    def test_candidate_symlink_and_failed_validation_leave_source_unchanged(self):
        self.prepare()
        before = sync.snapshot(sync.files(self.root))
        (self.stage / 'tree/escape').symlink_to(self.root / 'docs/UPSTREAM.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            sync.apply(self.root, self.stage, True)
        (self.stage / 'tree/escape').unlink()
        (self.stage / 'tree/docs/UPSTREAM.json').unlink()
        with self.assertRaisesRegex(ValueError, 'lacks upstream metadata'):
            sync.apply(self.root, self.stage, True)
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))

    def test_validator_failure_does_not_apply_metadata(self):
        self.put('agents/new.md', 'incoming agent\n')
        self.commit()
        self.prepare()
        before = sync.snapshot(sync.files(self.root))
        (self.stage / 'tree/invalid').write_text('invalid')
        with self.assertRaises(subprocess.CalledProcessError):
            sync.apply(self.root, self.stage, True)
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))

    def test_file_directory_conflict_keeps_local_and_upstream_artifacts(self):
        name = 'skills/remove/file.md'
        self.write(name, 'local edit\n')
        (self.source / 'pstack' / name).unlink()
        self.put(name + '/new.md', 'incoming child\n')
        self.commit()
        plan = self.prepare()
        self.assertIn({'path': name, 'kind': 'file/directory'}, plan['conflicts'])
        self.assertEqual('local edit\n', (self.stage / 'tree' / name).read_text())
        self.assertEqual('incoming child\n', (self.stage / 'conflicts/upstream' / name / 'new.md').read_text())
        (self.stage / 'tree' / name).unlink()
        sync.write_tree(self.stage / 'tree', {name + '/new.md': (b'incoming child\n', 0o644)})
        plan['conflicts'] = []
        (self.stage / 'plan.json').write_text(json.dumps(plan))
        sync.apply(self.root, self.stage, True)
        self.assertEqual('incoming child\n', (self.root / name / 'new.md').read_text())

    def test_candidate_node_modules_are_rejected(self):
        self.put('agents/new.md', 'incoming agent\n')
        self.commit()
        self.prepare()
        path = self.stage / 'tree/skills/example/node_modules/pkg/index.js'
        path.parent.mkdir(parents=True)
        path.write_text('installed\n')
        before = sync.snapshot(sync.files(self.root))
        with self.assertRaisesRegex(ValueError, 'Installed dependencies'):
            sync.apply(self.root, self.stage, True)
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))
        self.assertTrue(path.exists())

    def test_excluded_occupant_blocks_apply_before_any_write(self):
        self.put('assets/binary', b'incoming\0image')
        self.put('assets/zz-collision', 'incoming file\n')
        self.commit()
        self.prepare()
        self.write('assets/zz-collision/node_modules/local.txt', 'keep me')
        before = sync.snapshot(sync.files(self.root))
        with self.assertRaisesRegex(ValueError, 'Path layout conflict'):
            sync.apply(self.root, self.stage, True)
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))
        self.assertEqual('keep me', (self.root / 'assets/zz-collision/node_modules/local.txt').read_text())

    def test_failed_write_restores_contents_modes_and_removed_files(self):
        self.put('assets/binary', b'incoming\0image')
        self.put('assets/zz-failure', 'incoming file\n')
        (self.source / 'pstack/skills/remove/file.md').unlink()
        self.commit()
        self.prepare()
        before = sync.snapshot(sync.files(self.root))
        original = sync.write_tree

        def fail(root, tree):
            if 'assets/zz-failure' in tree:
                original(root, tree)
                raise OSError('injected write failure')
            original(root, tree)
            if 'assets/binary' in tree:
                (root / 'assets/binary').chmod(0o755)

        with patch.object(sync, 'write_tree', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'injected write failure'):
                sync.apply(self.root, self.stage, True)
        self.assertEqual(before, sync.snapshot(sync.files(self.root)))

    def test_command_error_includes_stderr(self):
        with self.assertRaisesRegex(ValueError, 'authenticate with gh auth login'):
            sync.command(sys.executable, '-c',
                         'import sys; sys.stderr.write("authenticate with gh auth login"); sys.exit(1)')

    def test_github_api_puts_the_token_in_a_header(self):
        captured = {}

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class Opener:
            def open(self, request, timeout=None):
                captured['authorization'] = request.get_header('Authorization')
                captured['url'] = request.full_url
                return Response(b'{}')

        with patch.dict(os.environ, {'GH_TOKEN': 'sent-in-header', 'GITHUB_TOKEN': ''}):
            with patch.object(sync.urllib.request, 'build_opener', return_value=Opener()):
                self.assertEqual(sync.github_api('repos/cursor/plugins/commits/main'), b'{}')
        self.assertEqual(captured['authorization'], 'Bearer sent-in-header')
        self.assertNotIn('sent-in-header', captured['url'])

    def test_github_api_requires_a_token(self):
        with patch.dict(os.environ, {'GH_TOKEN': '', 'GITHUB_TOKEN': ''}):
            with self.assertRaisesRegex(ValueError, 'GH_TOKEN'):
                sync.github_api('repos/cursor/plugins/commits/main')

    def test_archive_downloads_upstream_without_gh(self):
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode='w') as tar:
            data = b'hello\n'
            info = tarfile.TarInfo('cursor-plugins-abc/pstack/LICENSE')
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
        responses = [json.dumps({'sha': 'a' * 40}).encode(), payload.getvalue()]

        def fake(path):
            self.assertNotIn(' ', path)
            return responses.pop(0)

        with patch.object(sync, 'github_api', side_effect=fake):
            sha, tree = sync.archive(None, 'main')
        self.assertEqual('a' * 40, sha)
        self.assertEqual(b'hello\n', tree['LICENSE'][0])
        self.assertEqual([], responses)

    def test_archive_rejects_symlinks(self):
        (self.source / 'pstack/agents').mkdir()
        (self.source / 'pstack/agents/escape').symlink_to('/tmp')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'Non-regular archive entry'):
            self.prepare()
        self.assertFalse(self.stage.exists())


if __name__ == '__main__':
    unittest.main()
