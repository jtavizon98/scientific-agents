# Session brief: <name>

Use the full session record for delegated, unattended, cross-host,
consequential, long-running, substantial, or recovery-worthy work. Routine
interactive work may remain lightweight.

## Objective and deliverables

State one reviewable outcome and the paths or external results that must exist.
Name the intended reader or user and the acceptance evidence.

## Ownership and scope

- Parent session and owner: `<none or session ID and owner>`
- Control client: `<where the user or coordinator interacts>`
- Agent runtime/writing host and mode: `<literal host; plan or build>`
- Execution targets: `<none or exact hosts/services>`
- Repository/worktree and starting ref: `<path; branch @ sha>`
- Native session identity: `<harness session ID; Herdr pane if any>`
- Allowed writes: `<explicit paths>`
- External read/write roots: `<none or exact preflighted roots>`
- Classification and destination: `<content class; approved repository/service/local-only>`

One writing owner, branch, and worktree apply unless this brief says
otherwise. Do not read credentials, personal data, high-volume mounts, or
unclassified material.

## Completion contract

- Final human review artifact: `<none or source and rendered artifact paths>`
- Required reviews: `<runtime/numerical/source/copy/build/visual/etc.>`
- Delivery: `<local path or authorized method and destination>`
- Blocker escalation: `<none, Herdr, or authorized method/destination>`
- Completion notification: `<none, Herdr, or authorized method/destination>`
- Human review closes task: `<yes for substantial reports or explicit exception>`
- Complete only when: `<one end-to-end completion sentence>`

Remote job completion is an intermediate checkpoint unless it is the entire
user-facing outcome. Apply the long-job procedure
(`long-job-continuation` skill) when a job may outlive one
interactive step.

## Evidence and decisions

- **Required:** `<source commitment>`
- **Observed:** `<verified fact and source>`
- **Assumed:** `<fact still requiring verification>`
- **Proposed:** `<choice not yet accepted>`

## Consequential authorization

- Authorized action and exact target: `<none or exact scope>`
- Authorized by/source/time: `<identity, instruction, ISO-8601 timestamp>`

Leave authorization as `none` until the user authorizes the named action.
Implementation authority is not automatically publication or submission
authority. A plan-to-build transition that expands scope must be recorded in
`STATE.md` before the newly permitted work begins.

## Verification and stopping conditions

- `<scoped command or review>`
- Confirm no out-of-scope paths changed.
- Stop on host or target mismatch, unknown dirty state, missing classification,
  credential requirements, destructive ambiguity, or work beyond scope.
- Update `STATE.md` at major checkpoints and before handoff or interruption.
- After compaction, restore every completion-contract gate in the active todo
  list before continuing.
