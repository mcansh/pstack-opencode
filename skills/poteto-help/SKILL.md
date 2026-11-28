---
name: poteto-help
description: Explain pstack for OpenCode setup, skill selection, playbooks, and runtime limits. Use when asked how to use this workflow pack.
metadata:
  opencode/autoinvoke: false
---

# Poteto help for OpenCode

Read [OpenCode runtime contract](../opencode-runtime.md) first.

For a help request, read [README](../../README.md) and answer without starting the task. For a work request, read [poteto-mode](../poteto-mode/SKILL.md) and do the authorized work.

- Setup and role models: [setup-pstack](../setup-pstack/SKILL.md).
- Rewrite a prompt before sending it: [sharpen](../sharpen/SKILL.md). Returns a deeper prompt with expert methods, raw sources, and an outside check. The rewrite asks for experiments to settle empirical choices while leaving product and preference decisions to the user; it does not execute the task.
- Find the expert words for what you're building: [`/pstack:reframe`](../reframe/SKILL.md). Checks sources where accessible, borrows useful terms from neighboring fields, and rewrites your description without doing the task.
- Understand code or rationale: [how](../how/SKILL.md), [why](../why/SKILL.md). How uses one read-only delegate when available. Why starts with commits and PR discussions and widens the search when that trail is thin.
- Design alternatives: [architect](../architect/SKILL.md), [arena](../arena/SKILL.md). Architect sketches two shapes, using Arena for large or contested designs.
- Review and impact: [interrogate](../interrogate/SKILL.md), [blast-radius](../blast-radius/SKILL.md). Interrogate keeps findings proven by rerunning safe repros, lists dropped findings, and applies no fixes.
- Parallel work: [swarm](../swarm/SKILL.md). Requires available agent tools and respects their capacity.
- App proof: [create-verification-skill](../create-verification-skill/SKILL.md), [maintain-verification-skill](../maintain-verification-skill/SKILL.md).
- Formal proof: [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md), [maintain-formal-verification-skill](../maintain-formal-verification-skill/SKILL.md). Use for races or invariants tests rarely reach; maintain checks when covered code changes.
- Behavior charts: [statechart](../statechart/SKILL.md). Draw model-checked user flows with the shortest path to each state that breaks a rule.
- Chat updates and decisions: [ketchup](../ketchup/SKILL.md). Lists every pending user decision with evidence and risk.
- Video catch-up: [ketchup-video](../ketchup-video/SKILL.md). Produces subtitled slides when video rendering and frame inspection are available; pending decisions remain in text.
- Prior work: [recall](../recall/SKILL.md). Uses only exposed in-scope history.
- Personal style and lessons: [automate-me](../automate-me/SKILL.md), [reflect](../reflect/SKILL.md). Reflect mines the active transcript directly and proposes edits for approval.

Playbooks belong to poteto-mode, not separate slash commands. Read its index to select the matching workflow. Use `/pstack:poteto-mode` plus a concrete goal and a pass/fail check, or ask the agent to load `pstack-poteto-mode` with its skill tool. Autopilot-stack builds verified PRs without merging; it stacks only changes that depend on another PR. The former Orchestrate playbook is retired; project-scale work routes to figure-it-out within the runtime's lifetime limits. Babysit never rebases, retargets, or force-pushes; it reports the branch needing a rebase and stops. Plans wait for explicit execution authority.

Defaults use native OpenCode agent inheritance without a model override. Different-model panels require actual configured models; Arena skips its judge when no configured agent meets the different-family and different-vendor checks. Cloud agents, persistent loops, Cursor Custom Modes, Grok Bot routines, Benny automations, and the upstream Claude Code adapter are not supplied by this port. A session without delegates can work sequentially, but cannot claim independent verification. See [compatibility](../../docs/COMPATIBILITY.md).

Check setup only when it changes the answer. If `~/.config/pstack/opencode-models.md` is missing, roles use the default delegate. For setup or cost questions, offer [setup-pstack](../setup-pstack/SKILL.md) once. A shorter panel list uses fewer attempts, one per entry. Reasoning and speed changes require supported native agent settings, not generated model names. For runtime proof questions, check for a project verification skill. For races or invariants, check for a formal verification skill and whether its recorded revision still covers the code.

Keep the answer short. Give one concrete prompt when helpful and link the actual checkout file. Use `/pstack:` commands in user-facing examples. Archived `docs/upstream/` pages describe the upstream hosts, not this fork's runtime.
