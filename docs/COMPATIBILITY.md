# OpenCode plugin compatibility

This package is a native OpenCode v2 server plugin with ID `pstack`. Load it through the normal `plugins` configuration array. It uses the existing OpenCode binary and configuration.

| Capability | Adaptation |
| --- | --- |
| Skills | Plugin skill transforms register bundled content with absolute paths and invocation metadata. |
| Commands | Plugin command transforms derive entry points from non-principle skills. Original prompt attachments, mention offsets, and delivery are preserved. |
| Delegate prompts | Bundled Markdown is passed to an exposed general agent. The v2.0.24 plugin API cannot create new agents. |
| Models | Existing OpenCode agent settings control model choices. Role maps are read on demand. |
| Permissions | Existing OpenCode permissions remain authoritative. |
| History | Active or explicitly supplied in-scope history only. |
| Portable helpers | Worktree audit, orchestration ledger, PR watch, statechart, and upstream staging remain bundled. |
| Cloud and scheduling | Require separate host capabilities. |

The plugin does not change default agents, providers, permissions, or user configuration files. Skills use `pstack-` IDs and commands use `pstack:` names to avoid collisions with unrelated registrations. Cursor services and hosted Codex subscription automation are not implemented.

OpenCode v1 is unsupported. The package uses Bun's built-in YAML parser, matching OpenCode's runtime, and needs no additional runtime dependencies.

See [verification](VERIFICATION.md) for source and packaged plugin checks. Native registration does not prove behavioral compliance by a model.
