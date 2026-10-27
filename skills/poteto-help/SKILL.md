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
- Rewrite a prompt before sending it: [sharpen](../sharpen/SKILL.md). Returns a deeper prompt with expert methods, raw sources, and an outside check; leaves execution to a later request.
- Understand code or rationale: [how](../how/SKILL.md), [why](../why/SKILL.md).
- Design alternatives: [architect](../architect/SKILL.md), [arena](../arena/SKILL.md).
- Review and impact: [interrogate](../interrogate/SKILL.md), [blast-radius](../blast-radius/SKILL.md).
- Parallel work: [swarm](../swarm/SKILL.md). Requires available agent tools and respects their capacity.
- App proof: [create-verification-skill](../create-verification-skill/SKILL.md), [maintain-verification-skill](../maintain-verification-skill/SKILL.md).
- Formal proof: [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md), [maintain-formal-verification-skill](../maintain-formal-verification-skill/SKILL.md). Use for races or invariants tests rarely reach; maintain checks when covered code changes.
- Behavior charts: [statechart](../statechart/SKILL.md). Draw model-checked user flows with the shortest path to each state that breaks a rule.
- Chat updates and decisions: [ketchup](../ketchup/SKILL.md). Lists every pending user decision with evidence and risk.
- Video catch-up: [ketchup-video](../ketchup-video/SKILL.md). Requires an available video renderer and frame inspection tools; pending decisions remain in text.
- Prior work: [recall](../recall/SKILL.md). Uses only exposed in-scope history.
- Personal style and lessons: [automate-me](../automate-me/SKILL.md), [reflect](../reflect/SKILL.md).

Playbooks belong to poteto-mode, not separate slash commands. Read its index to select bug fix, feature, refactoring, performance, shipping, babysit, or orchestration. Use `/pstack:poteto-mode` plus a concrete goal and a pass/fail check, or ask the agent to load `pstack-poteto-mode` with its skill tool.

Defaults inherit the current OpenCode model. Different-model panels require actual supported models. Cloud agents, persistent loops, Cursor Custom Modes, Grok Bot routines, and Benny automations are not supplied by this port. A session without delegates can work sequentially, but cannot claim independent verification. See [compatibility](../../docs/COMPATIBILITY.md).

Check setup only when it changes the answer. If `~/.config/pstack/opencode-models.md` is missing, roles inherit the parent model. For setup or cost questions, offer [setup-pstack](../setup-pstack/SKILL.md) once. For runtime proof questions, check for a project verification skill. For races or invariants, check for a formal verification skill and whether its recorded revision still covers the code.

Keep the answer short. Give one concrete prompt when helpful and link the actual checkout file.
