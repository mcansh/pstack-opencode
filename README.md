# pstack for OpenCode

A native OpenCode v2 plugin with pstack's engineering workflows, principles, review prompts, and verification helpers. MIT licensed, with original attribution to Lauren Tan.

## Install

Add this checkout's absolute path to the `plugins` array in your existing `~/.config/opencode/opencode.json` or project `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["/absolute/path/to/pstack-opencode"]
}
```

Merge this entry with your existing settings and plugins. Restart OpenCode or reload its configuration, then use the regular `opencode` command. No launcher, separate binary, symlinks, or replacement configuration directory is needed. The source repository is private at [mcansh/pstack-opencode](https://github.com/mcansh/pstack-opencode). The package has not been published to npm.

## Use

Run `/pstack:poteto-mode` with a concrete task. `/pstack:poteto-help` selects workflows; `/pstack:setup-pstack` configures model roles using existing OpenCode agents. Other commands include `/pstack:how`, `/pstack:why`, `/pstack:architect`, `/pstack:interrogate`, `/pstack:swarm`, and `/pstack:statechart`.

The plugin registers 58 skills and 34 commands through OpenCode's plugin API. Principles load on demand. Invocation metadata preserves explicit selection for skills that were manual in the source port. Registration uses the bundled files directly; commands do not need regeneration after skill changes. Skills use IDs such as `pstack-poteto-mode`, and commands use names such as `/pstack:poteto-mode`, avoiding collisions with your other skills and commands.

The two files in `agents/` are delegate prompts. OpenCode v2.0.24's plugin API cannot create agents. Workflows use an available general agent with those prompts unless you have configured a suitable named agent yourself. The plugin does not change your default agent, model, permissions, provider settings, or global files.

Read the [runtime contract](skills/opencode-runtime.md), [compatibility](docs/COMPATIBILITY.md), and [verification record](docs/VERIFICATION.md).

## Develop

Plugin execution and tests use OpenCode's Bun runtime and its built-in YAML parser. No additional runtime dependencies are needed.

```sh
bun test test/plugin.test.js
python3 scripts/check-plugin.py
python3 scripts/test-check-plugin.py
python3 scripts/check-native.py
python3 scripts/test-sync-upstream.py
```

The native check starts a disposable OpenCode server with a normal `plugins` configuration entry and verifies plugin activation, skill paths, invocation metadata, command registration, and preservation of unrelated settings. It makes no model calls.

Portable helper checks remain available:

```sh
cd skills/poteto-mode/scripts
bun install --frozen-lockfile
bun run test
bun run typecheck
```

Statechart's suite runs with `bun install --frozen-lockfile && bun run test` from `skills/statechart/scripts`. TLC integration needs Java 11 or later and `TLA2TOOLS` pointing to `tla2tools.jar`.

## Scheduled upstream sync

[Sync upstream pstack](.github/workflows/sync-upstream.yml) checks `cursor/plugins` every two hours at minute 17 UTC. You can also run it manually from Actions. Existing update PRs are preserved; unchanged upstream content skips adaptation. Pullfrog adapts changes to the OpenCode contract, checks the result, and opens a draft PR on `automation/sync-upstream`. It does not merge automatically.

The automation uses the same Pullfrog ChatGPT/Codex subscription integration as `pstack-codex`. The agent adapts OpenCode plugin content; the runtime plugin continues to run in OpenCode. Repository access for the Pullfrog GitHub App and a connected subscription are required. In the Pullfrog repository console, select **Custom (set in workflow)** for the model. The workflow defaults to `openai/gpt-sol`; set `UPSTREAM_SYNC_MODEL` to override it. No local authentication files or API keys are copied into this repository.

Enable **Allow GitHub Actions to create and approve pull requests** in repository Actions settings. The adaptation job has read-only source access and restricted agent pushes. A separate publishing job can create the bounded update PR after validation.

[Check plugin](.github/workflows/check.yml) runs package, plugin registration, synchronization, and workflow policy checks on pushes to `main` and pull requests, on this repository's self-hosted Mac runner (`self-hosted`, `macOS`, `ARM64`). Whether a fork pull request starts that job depends on the repository's fork-workflow settings, not on the repository being private. [Sync upstream pstack](.github/workflows/sync-upstream.yml) is `schedule` and `workflow_dispatch` only, and its adaptation job runs only on the default branch. Adaptation stays on GitHub-hosted `ubuntu-latest` because the pinned Pullfrog action's restricted shell needs Linux `unshare` PID namespaces. Hosted runners are currently blocked by GitHub billing, so adaptation waits until that is resolved. The publish job stays on the Mac runner: it downloads the validated patch artifact and opens the draft PR. Checksums use `shasum`.

## Upstream

Use the repository's [sync-upstream skill](.opencode/skills/sync-upstream/SKILL.md) to stage and review updates from `cursor/plugins`. Keep the runtime contract and plugin API adaptations when merging. [PORT.json](docs/PORT.json) records the Codex source revision; [UPSTREAM.json](docs/UPSTREAM.json) retains original pstack provenance. The [historical upstream guide](docs/upstream/README.md) describes Cursor.

See OpenCode's official [plugin installation](https://opencode.ai/v2/docs/build/plugins/) and [server plugin API](https://opencode.ai/v2/docs/build/plugins/server) documentation. This package targets OpenCode v2.0.24 and has no V1 implementation.
