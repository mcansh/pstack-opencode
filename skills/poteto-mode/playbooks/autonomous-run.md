### Autonomous run

**You own the exit condition. Define done, then drive to it without stopping.**

1. State the exit condition as a checkable predicate and declare a finite time or iteration budget before the first iteration (tests green, repro fixed, all N authorized PRs merged, pixel-diff zero).
2. Pick the wake mechanism using a bounded in-session loop with the available wait or status tools. An event to watch (CI, a merge, a ref advancing) may get a watcher delegate only if supported and permitted. Size each wait to the remaining budget. Select supported native agent settings per the Subagents section. Do not assume a built-in `/loop` or persistent scheduler exists.
3. Each iteration makes the smallest change the evidence justifies and verifies it against the predicate. Commit only when authorized. Discard only this run's failed experiments, never the user's or another agent's work.
   Sequence the work via the **sequence-verifiable-units** principle skill, verifying each unit before the next instead of batching checks at the end.
4. Fix discoveries that support the goal only within the authorized scope. Record unrelated bugs, broken skills, and other follow-ups instead of starting another workflow or publishing a separate PR without authority. A full-autonomy grant does not remove host permissions or approval gates. Keep the predicate as the main drive.
5. Checkpoint every iteration via the **show-me-your-work** skill, a row for what changed and whether the predicate moved.
6. Stop when the predicate is met, the declared budget expires, the user stops the run, or a permission blocker prevents progress. Checkpoint unfinished work and name the blocker. Pivot within the budget rather than spinning, and never relax the predicate to declare victory. Persistence beyond the session requires an exposed authorized scheduler.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
