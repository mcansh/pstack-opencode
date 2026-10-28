---
name: setup-pstack
description: Configure pstack roles using registered OpenCode agents and their supported models. Use for setup, model choices, or cost changes.
---

# Setup pstack for OpenCode

Read [OpenCode runtime contract](../opencode-runtime.md) first.

1. Inspect the current task tool schema and registered agents. Inspect `opencode models` for available provider/model identifiers when a model change is requested. Do not print credentials or assume a listed provider is authenticated.
2. Read `~/.config/pstack/opencode-models.md` if present. Preserve supported role choices and unrelated entries. The default for every role is `inherit-parent`, which selects the default delegate without a model override, following native agent configuration rather than guaranteeing the parent's exact model. Explicit choices have the form `agent=<registered-name>`. A comma-separated panel value selects one seat per entry. Missing panel roles use two independent attempts, subject to host capacity.
3. For setup or cost changes, confirm the desired budget and role choices before writing. Upstream's unlimited, large, medium, and small budgets are preferences for supported native agent settings, not model-slug suffixes. Do not alter a configured model's effort or speed by inventing identifiers. Preserve current choices until a supported alternative is confirmed.
4. For a requested model override, configure a native OpenCode subagent with that exact supported model in the user's chosen project or global configuration only with authorization. Inspect existing settings first and preserve unrelated content. Do not guess a model, reasoning variant, or task-tool parameter. The plugin cannot create agents; bundled files under `agents/` remain prompt templates. Never relax permissions to make a role work.
5. Once the user's choices are clear, write the role map. For example, `how explorer: inherit-parent` or `interrogate reviewers: agent=review-a, agent=review-b`. This file is read on demand by pstack and is not loaded by OpenCode itself. Missing roles inherit. Report a missing named agent; use the default only with the limitation disclosed. For `arena cross-judge pool`, preserve list order and select only an available agent whose known model family differs from the parent's; otherwise skip the judge and mark that gate unverified.
6. Report changed paths and validate that OpenCode loads the configured agents. Same-model reviewers are independent attempts. Different-model evidence requires agents configured with different models. Missing task permissions or delegation support cannot be enabled by a role map. If agent loading cannot be tested, report it as unverified.
7. Check for existing [runtime verification](../create-verification-skill/SKILL.md) and [formal verification](../create-formal-verification-skill/SKILL.md) workflows. Offer a missing kind once when relevant. Generate only the requested kind.
