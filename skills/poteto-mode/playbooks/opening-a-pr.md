### Opening a PR

Use after another playbook only when the user's request authorizes publication. Completion of local work is not permission to commit, push, or open a PR.

Work from an exclusive git worktree off trunk, and keep unrelated work out of it. Pass its absolute path to writers and verify their working directory; delegation does not create isolation. Preserve dirty and unrelated work. Never reset or discard it to make this workflow run.

Commit only when authorized. Prefer small, landable commits. Rebasing, amending, or rewriting existing history requires the necessary authority and must preserve other writers' work. Run a diff simplification review per the OpenCode runtime contract before commit and **no-comments** before review. Apply **technical-writing** and **unslop** to the PR text and commit bodies.

Title: `type(scope): subject`, naming a real symbol when one carries the change. Body: a one-minute briefing under 40 lines with these `##` headings in order, dropping empty ones: `## Why`, `## What changed`, `## Scope`, `## Tradeoffs` (only rejected alternatives a reviewer would otherwise ask about), `## Blast Radius`, `## Verification`. Evidence logs, histories, and long tables go in a linked artifact, not the body.

Resolve the forge before the first PR operation and keep that choice. Use required host PR tools for the operations they cover. Otherwise use `gh` by default, or `origin pr` when Origin's CLI resolves the repository. Never require Graphite (`gt`).

Stack follow-ups by base branch. The root targets trunk; a dependent child targets its parent's branch. Branch from trunk for independent work. Coordinate stack mutations with the exclusive branch owner. Every changed head needs fresh CI and verification against its current base.

Open PRs ready by default when publication is authorized, but preserve an explicit user request for a draft and any repository policy. Inspect the actual PR-tool schema rather than assuming it accepts `draft`. When it does, use `draft: false` for ready and `draft: true` for a requested draft. Without a host tool, use `gh pr create` without `--draft`, or `origin pr create --status open`, for ready. Never mark an existing draft ready without authority. Read back the actual PR status before reporting it.

Opening a PR does not start a babysit. Return the URL and keep building the authorized work. An Autopilot owner's brief may separately authorize a bounded babysit loop after its code-ready report, subject to `playbooks/babysit.md`. Babysitting itself never rebases or force-pushes.
