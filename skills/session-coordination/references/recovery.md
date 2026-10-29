# Startup and recovery

A read-only-first procedure for returning to an agent runtime after an
interruption: unexpected disconnect, harness crash, lost terminal-multiplexer
session, expired SSH master, reboot. Recovery means finding durable work and
choosing what to resume. It does not authorize automatic continuation of an old
autonomous prompt, and a reconnect does not authorize old queued actions.

Manual recovery is the operating model. Do not schedule a disruptive reboot
only to test it. Record evidence when the next natural interruption occurs and
improve this procedure from what actually happened.

## Recover harness context, then verify it

Asking a harness directly to recall an earlier session through its database,
history, or other supported mechanism often works. Use that as a first lead,
not as proof of current state.

Before resuming, reconcile the recalled context against:

1. the chosen session's `BRIEF.md`, `STATE.md`, and `RESULT.md` when present;
2. the owning Git branch and worktree;
3. live Herdr agents and any fallback tmux sessions;
4. read-only status of any remote jobs.

For sessions with long-running jobs, also reconcile the completion contract of
the [long-job procedure](../../long-job-continuation/SKILL.md). Restore the full chain from job monitoring through
output validation, report production, required reviews, and requested
notification; do not recover only the step that was active at compaction or
disconnect.

Resume exactly one chosen session only when those sources agree and the prior
task is still desired. Update `STATE.md` with the new owner and checkpoint. If
the recalled context and durable evidence disagree, record the mismatch and
stop without changing jobs, credentials, or worktrees.

## Routine continuation and client changes

A phone/laptop attachment to the same live agent preserves its existing owner
and worktree. Verify the selected session and runtime before steering it; do not
start a second writer just because the visible client changed. For a transfer to
a different agent or harness, first checkpoint the outgoing owner, stop its
writing activity, reconcile durable state and Git, and explicitly assign the
receiving owner and next action. Use [Git coordination](git-coordination.md)
for source handoff. A UI reconnection does not itself authorize resuming a
stale autonomous task.

## 1. Establish connectivity and identify the host

```bash
hostname -f
date -Is
ssh -o BatchMode=yes -o ConnectTimeout=5 YOUR_SSH_ALIAS 'hostname -f; date -Is'
```

If non-interactive SSH fails, the user establishes one interactive master.
Never request a password or inspect/copy SSH credential configuration. See the
SSH invariants in [consequential actions](consequential-actions.md).

## 2. Check host health and the user session

```bash
uptime
df -h YOUR_WORK_DIR YOUR_SCRATCH_DIR
loginctl show-user "$USER" --property=State --property=Linger
```

Treat warnings as observations. Do not clean storage, change mounts, or alter
services from this checklist.

## 3. Inspect Herdr and harness status

If Herdr owns the agent panes, inspect the named server and its reported native
session identities to answer: is the service running, is a client attached, and
is the intended agent recoverable? Do not print environment variables, tokens,
config files, pane history, or transcripts. Do not start a harness merely
because it is stopped. Treat the local machine as the control client and the
remote host as the runtime host. See the [Herdr guide](../../../docs/clients/herdr.md).

## 4. Inspect fallback tmux state

```bash
tmux list-sessions
```

Tmux is for ordinary shells, unsupported cases, and rollback. It is not the
normal owner of a Herdr-managed agent. Attach only to a chosen known utility or
fallback session: `tmux attach -t NAME`. Never resume one native agent session
in tmux while Herdr owns it. If neither runtime has the intended agent, inspect
durable session files before creating one; an interruption may have ended the
process while leaving its work intact.

## 5. Inspect active session state

From the coordination checkout, use an explicit checkout-relative path. For
each known active session, read its `BRIEF.md` and `STATE.md`; do not
recursively scan unrelated home or mounted trees.

```bash
find SESSIONS_DIR -mindepth 2 -maxdepth 2 -name STATE.md -type f -print
```

Confirm the last checkpoint, completed work, blocker, next safe action, and
forbidden actions. A stale `in progress` marker is evidence to investigate,
not permission to resume automatically.

If monitoring was delegated, identify the parent and monitor session IDs, the
monitor deadline and handback state, and any superseded job attempts. Rebuild
the harness todo list from the durable brief and state when it omits a final
artifact, review, or notification requirement.

If programmatic monitors write status files, inspect their latest snapshot,
result and handoff files, and any wait state, result and notification records.
A wait that is `orphaned`, `notifying`, `notification_unknown`, `notified`, or
`notification_failed` is a durable completion queue, not authority to resume a
model automatically. Treat `notifying` as an uncertain external outcome: verify
the notifier stopped and reconcile the transport before marking it
`notification-unknown` or acknowledging it.

Check transient user units without changing them:

```bash
systemctl --user --no-pager --plain list-units 'YOUR_MONITOR_PREFIX-*'
```

An expired lease, absent unit, stale snapshot, or orphaned wait is evidence
requiring investigation. It is not permission to submit, retry, cancel, or
resume work. After explicitly choosing the owning parent, read its wait contract
and result, reconcile current external status, then acknowledge the event only
after its evidence has been consumed.

An orphaned result remains queued until an explicitly selected recovery owner
reconciles it. A `notifying` state without terminal notification evidence is
externally uncertain: do not retry delivery automatically. Restore or reassign
parent ownership before acknowledging the event, and remember that
acknowledgement does not validate outputs or complete the parent objective.

## 6. Inspect Git before any pull

In each selected checkout:

```bash
git status -sb
git branch -vv
git worktree list
git remote -v
```

Identify uncommitted work and ownership first. Do not pull from cron. If a
manual update is appropriate, fetch, inspect, and use a fast-forward-only pull;
do not overwrite divergence or another session's worktree. If you have a
workspace sweep tool, run it as a dry run only; a sweep finding does not
authorize automatic session recovery.

## 7. Check remote jobs and credentials without changing them

With the established SSH master, use read-only queue/status commands scoped to
the user. Check whether required credentials appear valid using status-only
commands documented by the owning workflow. Do not authenticate, renew a
proxy, submit, cancel, start, stop, or modify anything.

## 8. Resume one harness explicitly

Choose the session, control client, runtime host, worktree, and harness. Re-read
its brief and current state, confirm that the prior task is still desired, then
start or attach using that harness's documented procedure and resume only the
recorded native session identity. Update `STATE.md` immediately with the new
owner and checkpoint.

## Stop conditions

Stop before action when the host is unexpected, a worktree is dirty with an
unknown owner, state and Git disagree, credentials would need renewal, a job
action is implied, or recovery would overwrite/destroy information.
