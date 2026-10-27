#!/usr/bin/env python3
"""Exercise scheduled sync boundaries using disposable repositories."""
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('sync_action', Path(__file__).with_name('sync-action.py'))
action = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action)


class SyncActionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.stage = self.root / '.pstack/upstream-sync'
        self.original = self.root / '.pstack/prepared-plan.json'
        action.sync.write_tree(self.root, {
            'docs/UPSTREAM.json': (b'{"commit":"old"}\n', 0o644),
            'skills/example/SKILL.md': (b'old\n', 0o644),
            'scripts/protected.py': (b'protected\n', 0o644),
        })
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.com', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'initial')
        initial = action.sync.files(self.root)
        candidate = dict(initial)
        candidate['docs/UPSTREAM.json'] = (b'{"commit":"new"}\n', 0o644)
        candidate['skills/example/SKILL.md'] = (b'new\n', 0o644)
        action.sync.write_tree(self.stage / 'tree', candidate)
        self.plan = {'schema': 1, 'target': 'new', 'baseline': 'old',
                     'initial': action.sync.snapshot(initial), 'changes': ['skills/example/SKILL.md'],
                     'conflicts': [], 'status': 'needs-review', 'tree': 'tree'}
        self.save_plan()
        self.original.write_text(json.dumps(self.plan))

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True).stdout

    def save_plan(self):
        (self.stage / 'plan.json').write_text(json.dumps(self.plan))

    def verify(self):
        return action.verify(self.root, self.stage, self.original)

    def test_repository_head_change_without_mapped_changes_is_noop(self):
        self.plan['changes'] = []
        self.save_plan()
        self.assertFalse(action.has_changes(self.stage))

    def test_mapped_change_is_detected(self):
        self.assertTrue(action.has_changes(self.stage))
        self.assertEqual(self.verify(), ['docs/UPSTREAM.json', 'skills/example/SKILL.md'])

    def test_forbidden_candidate_change_and_removal(self):
        path = self.stage / 'tree/scripts/protected.py'
        path.write_text('modified\n')
        with self.assertRaisesRegex(ValueError, 'outside upstream scope'):
            self.verify()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'outside upstream scope'):
            self.verify()

    def test_provenance_and_plan_are_immutable(self):
        (self.stage / 'tree/docs/UPSTREAM.json').write_text('{"commit":"other"}')
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.verify()
        self.plan['target'] = 'other'
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'plan field changed'):
            self.verify()

    def test_conflicts_markers_and_symlinks_are_rejected(self):
        self.plan['conflicts'] = [{'path': 'skills/example/SKILL.md'}]
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'Unresolved upstream conflicts'):
            self.verify()
        self.plan['conflicts'] = []
        self.save_plan()
        path = self.stage / 'tree/skills/example/SKILL.md'
        path.write_text('<<<<<<< upstream\n')
        with self.assertRaisesRegex(ValueError, 'conflict markers'):
            self.verify()
        path.unlink()
        path.symlink_to(self.root / 'scripts/protected.py')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.verify()

    def test_untracked_sources_and_working_drift_are_rejected(self):
        (self.root / 'unexpected.txt').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'Unexpected untracked'):
            self.verify()
        (self.root / 'unexpected.txt').unlink()
        (self.root / 'scripts/protected.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Working source changed'):
            self.verify()

    def test_opencode_runtime_files_are_preserved_and_never_exported(self):
        runtime_paths = ('.opencode/.gitignore', '.opencode/package.json', '.opencode/package-lock.json', '.opencode/bun.lock')
        for name in runtime_paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('runtime data\n')
        self.assertEqual(self.verify(), ['docs/UPSTREAM.json', 'skills/example/SKILL.md'])
        action.sync.write_tree(self.root, action.sync.files(self.stage / 'tree'))
        patch = self.root / '.pstack/patch'
        action.export(self.root, self.stage, self.original, patch)
        self.assertNotIn(b'.opencode/', patch.read_bytes())
        for name in runtime_paths:
            self.assertEqual((self.root / name).read_text(), 'runtime data\n')

    def test_opencode_configuration_and_skills_are_still_source(self):
        for name in ('.opencode/opencode.json', '.opencode/skills/example/SKILL.md'):
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('unexpected source\n')
                with self.assertRaisesRegex(ValueError, 'Unexpected untracked'):
                    self.verify()
                path.unlink()

    def test_candidate_node_modules_are_rejected(self):
        path = self.stage / 'tree/skills/example/node_modules/pkg/index.js'
        path.parent.mkdir(parents=True)
        path.write_text('installed\n')
        with self.assertRaisesRegex(ValueError, 'Installed dependencies'):
            self.verify()

    def test_export_contains_new_files_and_rejects_forbidden_removal(self):
        tree = action.sync.files(self.stage / 'tree')
        tree['agents/new.md'] = (b'new agent\n', 0o644)
        action.sync.write_tree(self.root, tree)
        patch = self.root / '.pstack/patch'
        action.export(self.root, self.stage, self.original, patch)
        self.assertIn(b'new file mode', patch.read_bytes())
        self.assertIn(b'agents/new.md', patch.read_bytes())
        replay = self.root / '.pstack/replay'
        self.git('worktree', 'add', '--detach', str(replay), 'HEAD')
        subprocess.run(['git', 'apply', str(patch)], cwd=replay, check=True)
        self.assertEqual(action.sync.snapshot(tree), action.sync.snapshot(action.sync.files(replay)))
        (self.root / 'scripts/protected.py').unlink()
        with self.assertRaisesRegex(ValueError, 'outside upstream scope'):
            action.export(self.root, self.stage, self.original, patch)


class SyncReviewPolicyTests(unittest.TestCase):
    def test_review_paths_keep_candidate_free_of_dependencies(self):
        repo = Path(__file__).resolve().parents[1]
        workflow_text = (repo / '.github/workflows/sync-upstream.yml').read_text()
        prompt = (repo / '.github/prompts/sync-upstream.md').read_text()
        skill = (repo / '.opencode/skills/sync-upstream/SKILL.md').read_text()
        names = re.findall(r'^      - (?:name: |uses: )(\S.*)$', workflow_text, re.MULTILINE)
        self.assertNotIn('Install candidate dependencies', names)
        self.assertLess(names.index('Adapt for OpenCode'), names.index('Validate and apply reviewed candidate'))
        self.assertLess(names.index('Validate and apply reviewed candidate'),
                        next(index for index, name in enumerate(names) if name.startswith('oven-sh/setup-bun@')))
        self.assertLess(next(index for index, name in enumerate(names) if name.startswith('oven-sh/setup-bun@')),
                        names.index('Install reviewed tool dependencies'))
        self.assertLess(names.index('Install reviewed tool dependencies'), names.index('Check reviewed tools'))
        self.assertLess(names.index('Check reviewed tools'), names.index('Export bounded update'))
        compact_prompt = re.sub(r'\s+', ' ', prompt)
        self.assertNotIn('running candidate checks', prompt)
        self.assertNotIn("Run the staged Bun tools' tests", skill)
        self.assertIn("Skip the skill's Bun test, typecheck, and apply steps", compact_prompt)
        self.assertIn('Do not run Bun tests, typecheck, `bun install`, `orch.ts`, or `watch-pr` against the candidate', skill)
        self.assertIn('Keep the candidate free of installed dependencies', compact_prompt)
        self.assertIn('Keep the candidate free of installed dependencies', skill)
        self.assertIn('After apply, install reviewed tool dependencies', skill)


if __name__ == '__main__':
    unittest.main()
