---
name: setup-pstack
description: Configure pstack roles using registered OpenCode agents and their supported models. Use for setup, model choices, or cost changes.
---

# Setup pstack for OpenCode

Read [OpenCode runtime contract](../opencode-runtime.md) first.

1. Inspect the current task tool schema and registered agents. Inspect `opencode models` for available provider/model identifiers when a model change is requested. Do not print credentials or assume a listed provider is authenticated.
2. Read `~/.config/pstack/opencode-models.md` if present. Preserve supported role choices. The default for every role is `inherit-parent`. Explicit choices have the form `agent=<registered-name>`. A comma-separated panel value selects multiple seats. Defaults use two independent attempts with the parent model.
3. For a requested model override, configure a native OpenCode subagent with that exact supported model in the user's chosen project or global configuration. Inspect existing settings first and preserve unrelated content. Do not guess a model, reasoning variant, or task-tool parameter. Model and provider settings belong to OpenCode agent configuration, not a Codex spawn call.
4. Once the user's choices are clear, write the role map. For example, `how explorer: inherit-parent` or `interrogate reviewers: agent=review-a, agent=review-b`. This file is read on demand by pstack and is not loaded by OpenCode itself. Missing roles inherit. A missing named agent is reported and falls back to the default only with that limitation disclosed.
5. Report changed paths and validate that OpenCode loads the configured agents. Same-model reviewers are independent attempts. Different-model evidence requires agents configured with different models. Missing task permissions or delegation support cannot be enabled by a role map.
6. Check for existing [runtime verification](../create-verification-skill/SKILL.md) and [formal verification](../create-formal-verification-skill/SKILL.md) workflows. Offer a missing kind once when relevant. Generate only the requested kind.
