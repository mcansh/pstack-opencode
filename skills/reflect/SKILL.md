---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
metadata:
  opencode/autoinvoke: false
---
Read [OpenCode runtime contract](../opencode-runtime.md) before executing this skill. It governs tools, models, settings, history, delegation, and authorization in all referenced files.


# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript in the conversation history explicitly exposed by the session. Use only explicitly exposed in-scope history, per the OpenCode runtime contract.

Use the active transcript returned by an available history tool or an explicit path from the session. Read its actual format before parsing. If none is exposed, pass a tight digest of the visible conversation.

## 2. Spawn three reviewers in parallel

Spawn three general-purpose reviewers with read-only scopes through the available agent tools, queuing them if needed. Reviewers need MCP access to look up the tickets, chat threads, and observability traces the transcript references, and connector access is determined by the environment.

Select the role named in the lens table below from `~/.config/pstack/opencode-models.md`, defaulting to `inherit-parent`, per the OpenCode runtime contract. Spawn the three lenses below, respecting the session capacity. Use only the actual agent-tool arguments and supported models; no vendor fallback or generated model slugs.

| Lens | Role line | Default `model` | Prompt template |
|---|---|---|---|
| Judgment | `reflect judgment, divergent, synthesizer` | `inherit-parent` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `inherit-parent` | `references/tooling-reviewer.md` |
| Divergent | `reflect judgment, divergent, synthesizer` | `inherit-parent` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their final report.

## 3. Synthesize

Spawn one read-only synthesizer using the `reflect judgment, divergent, synthesizer` role, defaulting to parent inheritance. It spot-verifies citations through MCP, and connector access is determined by the environment. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

Propose Backlog items. File them in a tracker only when the user authorized tracker writes.

Never edit a skill under `plugins/cache/`. Before approval, show its destination, `.agents/skills/<skill>/` or `~/.agents/skills/<skill>/`. After approval, copy the skill folder there and edit the copy. Preserve referenced resources or rewrite relative links to valid source paths, including the runtime contract and sibling skills. Validate every local link in the copied skill before finishing. Never open a PR or push.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to the available skill-authoring workflow skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `create-skill` and run its description-optimization loop.
- `new skill via create-skill: <kebab-name>`: hand creation to `create-skill`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
