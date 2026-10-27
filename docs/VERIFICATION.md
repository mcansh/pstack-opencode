# Verification

Checked on October 27, 2026 with OpenCode v2.0.24.

The initial launcher-based packaging was replaced with a native plugin after the user's correction. Earlier launcher and symlink checks are superseded by the plugin checks below.

| Check | Result |
| --- | --- |
| Native source plugin | Passed through a normal `plugins` configuration entry. Verified active pstack plugin, 58 namespaced skills, 34 namespaced commands, absolute asset paths, and invocation metadata. |
| Packed archive | Passed the same native checks after `npm pack` and extraction into a separate directory. |
| Existing configuration | Existing user agent and command retained in native checks. No default agent, model, provider, or permission mutation is implemented. |
| Plugin behavior | Bun test passed for registration, invocation policy, asset contents, prompt attachment preservation, mention offsets, and delivery mode. |
| Package links and worktree fixtures | Passed. |
| Upstream staging | All 13 regression tests passed after plugin repackaging. |
| Portable workflow helpers | Previous port run passed all 82 Bun tests and TypeScript check. Their implementation was not changed during plugin repackaging. |
| Full statechart suite | Previous bounded run was incomplete with 189 passes, 67 skips, and one cancelled CLI fixture after 45 seconds. Not rerun for this packaging correction. |

Rerun with `bun test test/plugin.test.js`, `python3 scripts/check-plugin.py`, and `python3 scripts/check-native.py`. To check a packaged install, pass its extracted directory as `--root` to the native checker.

Native verification uses a disposable local server and temporary configuration. It waits for this plugin's exact asset paths, not merely matching names from other installed skills. It terminates its own server and makes no model calls.

Delegate files are prompt templates. No unsupported agent-creation API is used. Skill IDs have a `pstack-` prefix and commands have a `pstack:` prefix because unqualified IDs can collide with existing skills loaded by OpenCode.

No authenticated model execution, cloud agents, hosted automation, PR operations, or deployment was tested. The npm package is unpublished. Repository publication and workflow status are reported separately from native plugin verification. See the [decision trail](../.audit/opencode-port.tsv).

## Repository automation

The private GitHub repository has been created. The upstream workflow checks every two hours with `17 */2 * * *` UTC and preserves existing draft update PRs. Local package, plugin registration, all 13 sync regressions, and all 9 workflow helper and policy tests passed before initial publication. Hosted execution is checked separately after pushing.

GitHub initially reported `can_approve_pull_request_reviews=false`. Automatic approval review rejected changing that broader setting without explicit permission. The user subsequently approved it, and the repository now reports `can_approve_pull_request_reviews=true` with default workflow permissions still set to `read`. Hosted plugin CI passed. The first upstream sync is running; completed draft PR publication has not yet been verified.
