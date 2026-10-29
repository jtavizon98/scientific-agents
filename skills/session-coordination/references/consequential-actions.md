# Consequential actions

Classify the operation before running it. User intent controls scope; recovery
checks do not create authorization.

| Level | Examples | Default handling |
| --- | --- | --- |
| Inspect | Status, logs, diffs, queue listing | Proceed read-only and scoped |
| Local reversible | Proposal edit, new branch, local test | Proceed within assigned boundary |
| Shared/recoverable | Push, manual remote pull, external report delivery | Verify target and explicit intent |
| Operational | Submit/cancel job, renew credential, mount/service change | Require explicit task authorization |
| Destructive/irreversible | Delete, overwrite, force-push, revoke | Verify recovery and obtain specific authorization |

## Measure twice, cut once

Before levels three through five, state:

- observed host and identity;
- exact target and current state;
- intended change and smallest correct command;
- owner and authorization;
- blast radius and dependents;
- rollback/recovery path and verification.

Record authorization durably in the active `BRIEF.md` or `STATE.md`: who
authorized the action, the source instruction, exact scope and target, and when
it was given. A status such as `authorized` without that evidence is not enough
to recover or transfer authority to another session.

An exact recorded authorization remains valid for the bounded sequence it
names. Do not ask the user to reapprove each atomic command merely because a
generic default is more restrictive. Recheck or ask again when the target,
scope, state, consequence, recovery path, or user instruction changes.

## Attempt failure and bounded recovery

A terminal attempt is not automatically a terminal authorization. When the
user authorized an implementation objective or bounded sequence, ordinary
technical recovery remains authorized if it preserves the same host, owners,
source and data identities, scientific behavior, mutation roots, resource
class, validation gates, claim limits, and recovery model. Examples include a
local environment-bootstrap correction, a quoting fix, or resuming from
preserved immutable outputs. Preserve the failed attempt, use a new attempt
identity and distinct evidence paths, recheck current state, and review the
delta in proportion to risk before continuing.

An agent-authored contract may make an attempt fail closed, but it must not
silently narrow broader user authority into a one-shot approval. A frozen hash
or exact command is an implementation and evidence-control mechanism unless
the user explicitly made that command or attempt count the authorization
boundary. A corrected hash or new attempt can require independent technical
review without requiring the user to approve it again.

Ask again when recovery changes a material boundary: host or external system,
repository/ref or source semantics, scientific or numerical target, accepted
input or artifact, release/toolchain beyond routine bootstrap, mutation
namespace or destructive cleanup, resource/cost class, publication/delivery,
credentials, or the promised claims. A new remote submission or other
operational side effect also needs coverage from the recorded task
authorization. Do not use a minor recoverable failure to manufacture an
approval stop.

Distinguish Git/source publication from external distribution. Building an
ignored local PDF is local reversible work. Emailing it, uploading it, or
otherwise delivering it outside the workspace is a separate shared action whose
destination and artifact must be authorized. Blocker escalation and completion
notification are also separate purposes even when one email performs both.

Preview when the tool supports it. Re-check immediately before action if time
or external state could have changed. Stop on ambiguity, an unexpected dirty
tree, missing recovery, or a target mismatch.

Guidance is a default, not a way to reject explicit user direction. An
override must still name the actual scope and cannot waive platform safety or
access constraints.

## Cleanup authorization

A cleanup tool may remove items that are provably disposable without
per-item approval, for example clean, idle linked worktrees whose branch a live
`git ls-remote` confirms, provided the tool rechecks each target first. Every
other deletion in a cleanup report needs the user's approval of that exact
report (its hash or equivalent), recorded in the active `STATE.md` before the
approval flag runs. Approval of a workflow or general cleanup objective is not
approval of a report.

## SSH control-master safety

These invariants apply to inspect-level commands as well as consequential
actions, and belong in the root instructions so every session loads them before
remote work:

- One bounded SSH call at a time per control master.
- Never kill, replace or recreate the user's SSH master.
- On a failed `BatchMode` probe, ask the user for one interactive login. Never
  handle, request or copy passwords or passphrases, and never inspect SSH
  credential configuration.
- Submissions, cancellations and deletions need explicit intent.
- A failed network mount can hang filesystem calls. Inspect mounts read-only,
  never search them recursively, and never edit code through a mount.
