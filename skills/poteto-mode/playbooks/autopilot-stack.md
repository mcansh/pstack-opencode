### Autopilot-stack

Run the Autopilot-full playbook, but do not merge, close PRs, or arm auto-merge. Publication still requires authority for the queue. Keep the parent playbook's runtime, permission, and bounded-lifetime limits.

1. **In place of step 5, stop at verified.** Stop when each PR is verified and green at its current head, then hand the PRs to the operator. After the handoff, nobody pushes without the operator's go. Every loop tick prompt names this file, so each tick sees the no-merge rule.
2. **Stack a PR only when it builds on another PR.** This is the one exception to step 3. Base the PR on the other PR's branch in place of trunk, per **Size and stacks** in `playbooks/opening-a-pr.md`. In place of step 2's rebase onto trunk, each PR's exclusive owner rebases onto its parent PR's branch, and the stack root rebases onto trunk. Coordinate lower-head changes bottom-up without concurrent writers on one branch. Every resulting head needs green CI and verification against its changed base. An unchanged `git patch-id` alone does not preserve the verdict.

**Reply:** list each PR with its verdict, in place of what merged.
