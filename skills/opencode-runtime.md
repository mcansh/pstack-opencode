# OpenCode runtime contract

Read this before executing a bundled workflow. This contract replaces host-specific instructions throughout pstack, including playbooks, templates, and delegate prompts. System, user, repository, and OpenCode permission policies remain authoritative.

## Skills and commands

Load a skill with OpenCode's `skill` tool using its `pstack-` prefixed directory name, such as `pstack-poteto-mode`. The bundled commands provide `/pstack:poteto-mode`, `/pstack:how`, and other workflow entry points. A workflow's `/skill-name` notation means load `pstack-skill-name` or invoke `/pstack:skill-name`; a playbook name is not a separate command. Resolve sibling skills relative to the loaded skill file.

Install this directory through the `plugins` array in normal OpenCode configuration. The plugin registers bundled skills and commands without replacing configuration directories or writing user files. Skill paths point into this package, preserving relative references and scripts. Personal skills can live in `~/.config/opencode/skills/`; project skills can live in `.opencode/skills/`. Existing `.agents/skills/` locations are also supported. `metadata.opencode/autoinvoke: false` hides a skill from automatic selection while allowing explicit loading. OpenCode permissions control access.

## Delegation and models

Use the task/delegation tool actually exposed by the running OpenCode version. Inspect its schema. Do not assume Codex spawn tools, Cursor `Task` arguments, `generalPurpose`, `run_in_background`, `readonly`, `environment`, or `cloud_base_branch` exist. This plugin ships `agents/poteto-agent.md` and `agents/comment-sicko.md` as prompt templates, not registered agents. Use a suitable exposed general agent and include the appropriate prompt. A user-configured named agent may be used when available. Supply the absolute poteto-mode skill path and an explicit scope in each prompt. If those agents are unavailable, use a suitable exposed general agent and include the prompt from `agents/poteto-agent.md`.

Models are configured on native OpenCode agents. An omitted agent model inherits according to OpenCode's current configuration. Read `~/.config/pstack/opencode-models.md` if present. This is an on-demand role map, not an OpenCode settings file. `inherit-parent` selects the default delegate without a model override. `agent=<registered-name>` selects an existing configured agent. Old workflow references to model families, reasoning effort, or speed are preferences, never literal task-tool arguments. Use `/pstack:setup-pstack` to map preferences to supported agents. Do not invent model IDs or pass `model` or `reasoning_effort` to a tool that does not accept them.

Same-model panels provide independent attempts, not model diversity. A different-family gate requires available configured agents using different model families. If unavailable, record that gate as unverified. Never silently substitute a provider.

Respect task permissions, agent depth, concurrency limits, and any prohibition on delegation. Give writers exclusive files or separate worktrees. Delegation does not create isolation. If delegation is absent or prohibited, work sequentially and disclose reduced independence. Never label self-review as independent verification.

## Tools, permissions, and history

Map upstream Read, Grep, Shell, AskQuestion, and todo operations to the available OpenCode read/search/bash, question, and todo tools. If a structured tool is unavailable, use a concise checklist or ask in chat. Inspect actual MCP availability and agent permissions. Read-only intent does not imply a particular MCP policy.

`create-skill` means valid skill authoring with YAML name and description, working relative links, and behavioral checks. `deslop` means simplifying the diff. `control-ui` and `control-cli` mean available browser, native, or terminal drivers. Report missing runtime evidence as unverified.

Use only the active conversation and explicitly supplied in-scope history. Session APIs are not permission to enumerate unrelated private conversations. Do not assume Codex JSONL or Cursor transcript paths. Timestamps do not establish liveness; use exposed agent status before cleaning worktrees.

## Execution lifetime

Cloud placement requires an exposed, documented, authorized remote service. Local tasks do not provide VMs or survive server shutdown by promise. Persistent loops require an external scheduler. `/loop` means a bounded loop in this session unless the host provides more. Store durable progress in a project-local, gitignored `.pstack/` directory when no store is supplied. Grok Bot, Benny automations, and Cursor cloud APIs are not supplied by this port.

## Authorization

Installing a workflow grants no permission to publish, merge, deploy, delete data, send messages, file issues, change account settings, or relax OpenCode permissions. Follow the user's actual request and host approval requirements. Preserve unrelated work and existing configuration. Never overwrite a conflicting skill or reset a dirty checkout to make installation work. Explicit permission already granted need not be requested again.
