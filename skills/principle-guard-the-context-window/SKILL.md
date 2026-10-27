---
name: principle-guard-the-context-window
description: "Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents; keep summaries in the main thread, not raw payloads."
metadata:
  opencode/autoinvoke: false
---
Read [OpenCode runtime contract](../opencode-runtime.md) before executing this skill. It governs tools, models, settings, history, delegation, and authorization in all referenced files.


# Guard the Context Window

**Why:** Context overflow degrades reasoning quality, creates compression artifacts, and halts progress.

**Pattern:**
- **Size phases and cap scope.** Limit files per phase, set turn budgets, account for mechanism costs.
