---
name: reframe
description: "Teach the expert words for what the operator is building, borrow words from neighboring fields that solved the same problem, then rewrite their description with them. Use for /pstack:reframe."
metadata:
  opencode/autoinvoke: false
---

Read [OpenCode runtime contract](../opencode-runtime.md) before executing this skill. It governs tools, models, settings, history, delegation, and authorization in all referenced files.

Teach the operator the expert words for what they are building. Start from their own description in this conversation and any files or code they supplied or put in scope, not a summary. Return a rewritten description without doing the task or editing files.

If their description could name more than one problem, first list the two or three problems it could be, each with the one term that names it and the sign that would tell it apart from the others. Then teach the words for the most likely one and say why you picked it.

1. Aim for 8 to 12 terms, ranked by how much each would change what gets built. For each, give the word and its meaning in one plain sentence, the part of their description it names, one real project, paper or system that uses it that way, with a link, and what it lets them ask an agent for.
2. Pick 2 or 3 neighboring fields that solved the same shape of problem under other names. For each, say what carries over, where the analogy breaks, and which terms come back.
3. Name what they didn't mention but should care about.
4. Rewrite their description with the new words.

Use available, permitted tools to open every cited source and confirm that it uses the term in the sense you describe. Use non-sensitive search terms; don't send private files, code, or conversation text to external services. Cut any citation you can't confirm. If source access is limited, say what you couldn't verify and distinguish provisional terms from sourced ones. No padding.
