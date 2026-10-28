---
name: interrogate
description: "Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"find blind spots\", or \"tear this apart\". Adversaries try to break a change or design, and only findings proven by a run survive."
metadata:
  opencode/autoinvoke: false
---
Read [OpenCode runtime contract](../opencode-runtime.md) before executing this skill. It governs tools, models, settings, history, delegation, and authorization in all referenced files.

# Interrogate

Adversaries try to break a change or a design. A finding survives only when a run proves it. Report the findings. Do not apply fixes to the user's checkout.

## Frame

The scope is what the user names. Otherwise it is the branch diff from its merge base with the base branch, through the working tree. State the intent with the **in-your-own-words** skill, from the user's message, the commits, and the PR description. Ask the user when the intent is unclear.

## Fan out

Run Phase A steps 3 and 4 and Phase B of the **arena** skill, with these changes. Read `interrogate reviewers` in place of `arena runners` from `~/.config/pstack/opencode-models.md`. Default to two `inherit-parent` seats without model overrides, using native agent configuration. Explicit entries select exposed agents as `agent=<registered-name>`. Same-model seats are independent attempts, not model diversity. Report unavailable entries and respect delegation permissions, depth, and capacity. If delegation is unavailable, work sequentially and disclose that the review is not independent.

Give each adversary a separate worktree or isolated disposable checkout. Copy only the scope's uncommitted changes into it without disturbing the user's work. An agent call alone does not create isolation. Use a suitable exposed general agent with the actual tool schema, not an assumed `generalPurpose` type. Include the absolute poteto-mode skill path and explicit scope. In place of the arena task and rationale, give each adversary the scope, the intent, and this brief:

> Break this change. Prove each finding with a run against the real code, such as a failing test, a repro script, or command output that shows the wrong behavior. For a design or plan, run a prototype or probe the current tree. Keep repros in your own worktree. Report each finding with a title, the exact command, the output it printed, and the output the intent requires. Leave out anything you did not run. That covers style, naming, structure, and risks that need a future change to matter. No findings is a valid result.

Every brief limits execution to authorized local probes in the isolated checkout. Read commands and scripts before running them. Do not publish, access unrelated conversations, expose secrets, change production data, or install dependencies without authorization. If safe execution or isolation is unavailable, report the affected coverage as unverified rather than running an unsafe repro.

## Verify

Verify each finding per arena Phase F by inspecting and safely rerunning its command in isolation. Keep a finding when the output shows the failure and the failure breaks the intent. Drop the rest. Merge findings that share a root cause. A command blocked by permissions or unavailable tooling is unverified, not evidence of safety.

Skip arena Phases C, D, and E. Adversaries find different failures, so the verdict keeps every verified finding, not one adversary's list.

## Output

- **Intent**: the restatement.
- **Reviewers**: the agents that actually ran, known model families, and any reduced independence or unavailable seats.
- **Findings**: for each verified finding, the command, its output, how it breaks the intent, and the adversaries that found it. Say "no verified findings" when none survive.
- **Dropped**: for each adversary, the count of dropped findings and why.
- **Unverified**: blocked commands, missing capabilities, and untested coverage. Do not turn these into a clean verdict.
