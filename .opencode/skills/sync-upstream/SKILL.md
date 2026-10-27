---
name: sync-upstream
description: Fetch upstream cursor/plugins pstack changes and adapt them for this OpenCode fork. Use in the pstack-opencode source repository when asked to sync or update from upstream.
---

# Sync upstream pstack

Run from the pstack-opencode source checkout. This workflow maintains the fork, so do not run it against an installed plugin cache.

Read [the compatibility table](../../../docs/COMPATIBILITY.md) and [the runtime contract](../../../skills/opencode-runtime.md) before adapting changes.

1. Run `python3 scripts/sync-upstream.py prepare`. Use `--ref <commit-or-branch>` for a requested revision. GitHub access requires authenticated `gh`. The command fetches the recorded baseline and an immutable target revision. It stages a three-way merge under `.pstack/upstream-sync` without changing working source files.
2. Read the generated `plan.json` and compare its `tree/` candidate with the working checkout. Resolve every reported conflict in the staged tree. For binary conflicts and modified upstream deletions, choose the intended file or deletion explicitly. Clear resolved entries from the plan's conflict list. Do not clear an entry without inspecting its upstream change.
3. Adapt incoming instructions to OpenCode in the staged tree. Three-way merges preserve existing edits but cannot establish semantic compatibility. Check model selection and inheritance, spawn arguments and agent limits, configuration paths, conversation access, authorization, remote execution, and persistent scheduling. New skills get a runtime pointer automatically, but their content still needs review. Read changed scripts as source. Do not execute candidate scripts or install their dependencies. Inspect ignored upstream paths for new capabilities that need an explicit OpenCode equivalent. Preserve the native plugin entry point, package metadata, and runtime contract. Plugin commands are derived directly from bundled skills at load time.
4. Run `python3 scripts/check-plugin.py --root .pstack/upstream-sync/tree`. Do not run Bun tests, typecheck, `bun install`, `orch.ts`, or `watch-pr` against the candidate; those commands install `node_modules` and can overflow review diffs. Keep the candidate free of installed dependencies. Review changed skills against the actual OpenCode capabilities exposed in this session. Report behavior requiring unavailable tools as unverified.
5. Run `python3 scripts/sync-upstream.py apply --reviewed` after resolving conflicts and reviewing compatibility. The command validates the candidate again and refuses changed working files. The recorded upstream revision advances only with the applied update. After apply, install reviewed tool dependencies and run the Bun tools' tests and typecheck when their code or lockfile changed. Inspect `git diff` and run `python3 scripts/check-plugin.py` against the working checkout.

Use a fresh `--stage <directory>` for a later sync. Existing stages are preserved so unfinished review is not overwritten. A failed validation or working-file drift leaves source files untouched. Do not publish, commit, or open a PR unless requested.

Report the old and new upstream revisions, adapted changes, validation results, and any skipped capabilities. A sync to the same revision is a successful no-op.
