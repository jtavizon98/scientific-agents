# Long-Running Job Monitoring

Use this workflow when remote jobs outlive one interactive work step, especially
when terminal outputs feed a human-facing report or completion notification.
Monitoring is one phase of the parent objective, not the objective itself.
The preferred continuation path is one parent-owned wait: the `monitor_wait`
tool in OpenCode, or one background `scripts/monitor_wait.py wait` task in
Claude Code. Polling runs in local programs and consumes no model calls or
delegated-agent tokens.

Script paths below are relative to this skill. `AGENT_SESSIONS_DIR` (default
`sessions`, relative to the project root) names the folder that holds one
subfolder per session; a wait contract must live directly in one of them.

## Client scope

The evidence, authorization, terminal-validation, and recovery contract applies
across clients. The wait backend, `monitor_wait.py wait`, takes an owner
`--harness {opencode,claude,codex}`, `--session-id`, and `--owner-pid`;
`--message-id` is required only for `opencode`. The harness is recorded in
`registration.json`.

- OpenCode: the `monitor_wait` tool supplies the identities. The plugin that
  provides it is `scripts/opencode-monitor-wait.ts`; see
  [OpenCode](../../../docs/clients/opencode.md). OpenCode permission settings
  below describe this integration.
- Claude Code (environment and background re-invocation verified; no live job
  wait yet): every Bash shell has `CLAUDE_CODE_SESSION_ID`
  and `CLAUDE_PID`. Run one command with `run_in_background`; Claude re-invokes
  the session when it exits, with no model polling:
  `python scripts/monitor_wait.py wait --harness claude --contract <path> --session-id "$CLAUDE_CODE_SESSION_ID" --owner-pid "$CLAUDE_PID" --timeout-seconds <N>`.
  Background tasks stop at 7,200,000 ms, so keep `<N>` below 7200. A
  `wait_timeout` result with monitors still active is a re-arm trigger, not a
  terminal failure: rerun with a fresh `--event-id` (a completed event returns its
  stored result). The notifier treats `CLAUDE_PID` as the liveness signal, so a
  closed Claude process orphans the wait for recovery.
- Codex: unverified. Remote control of a session does not verify unattended
  continuation. Do not invent identities; record the gap and use manual
  recovery of existing evidence.

Do not claim a durable callback exists for an unverified client.

## Slurm resource sizing and pending-job adjustments

Before every substantial submission, retrieve comparable prior session evidence
and scheduler accounting; do not copy an old allocation without checking usage.
Record requested CPUs, memory, walltime and array concurrency alongside
Submit/Eligible/Start/End, Elapsed, TotalCPU, MaxRSS and exit state. Distinguish
queue delay from dependencies or array concurrency limits, and failed startup
from successful processing. Use task-step accounting when MaxRSS is absent on
the parent job. Explain workload differences before transferring a resource profile.

Choose the smallest request supported by measurements with explicit memory and
time margin. Keep application threads aligned with allocated CPUs. Include all
sequential processing passes in walltime; their memory peaks do not add. Small
smoke tests do not establish full-input peak memory. Consult the project's own
documentation for application-specific configuration and execution commands.

Before moving a large job to another host, inspect exact input replicas,
cache locations, SSH gateway routing and destination capacity. Measure a bounded
representative transfer and include staging time in the host comparison; do not
infer throughput from NIC link speed or label one sample as a bandwidth cap.
Compare alternative authenticated routes without changing shared control masters.
Additional streams need disjoint files and measured aggregate improvement; they
do not automatically increase bandwidth. Keep one command at a time per shared
master, and let the user establish any required interactive authentication.

When a queue delay threatens the iteration loop, proactively compare the ask
with measured use and current scheduler settings. Smaller requests can improve
placement/backfill; whether they improve priority depends on site configuration.
Treat `sbatch --test-only` forecasts as nonbinding, not evidence that replacement
jobs will start sooner. Do not repeatedly poll through model calls: use the
existing programmatic monitor after a bounded diagnostic.

Prefer a supported in-place adjustment of still-pending jobs over cancellation
when it achieves the same reduction. Check the installed `scontrol` documentation,
owner, exact array indices and current state immediately before mutation. Do not
assume pending-job edits also work on running jobs. For example, the command
`scontrol update JobId=<id> MinMemoryNode=8192` can reduce a pending array to
8 GiB per task on a site that permits it; this is an example, never a reusable
target ID.
Verify every index and ReqTRES after the command, preserving before/after evidence
and the original submission script. Record scheduler overrides separately.

Apply adjustments within the recorded task authorization; if cancellation or
replacement is outside that scope, present a concrete recommendation first.
Cancellation/resubmission must also account for monitors, dependencies and
continuations bound to the old job ID. Do not assume queue-age priority is lost:
inspect the site's age weight. An in-place resource change retaining the same
job ID ordinarily requires no monitor rebinding.

## Durable completion contract

Before submission or delegated monitoring, record in the owning `BRIEF.md` and
`STATE.md`:

- the parent session and owner;
- exact job identifiers, host, scheduler or service, and evidence locations;
- authorized job actions and actions that remain forbidden;
- polling interval, monitoring time limit, and handback condition;
- terminal validation required before results may be used;
- every downstream private report, review, delivery, and Git/source publication
  gate;
- separate blocker-escalation and completion-notification targets and methods
  when requested;
- one explicit completion sentence.

Before leaving a processing-to-artifact continuation unattended, verify the
actual merge/build CLI against the pinned software revision and exercise it on
small representative artifacts. Successful event-processing smoke tests do not
validate later commands. Keep stage-specific recovery so a merge or plotting
failure resumes from completed immutable outputs instead of repeating expensive
processing. Preserve separate failure and eventual completion notification evidence.

The completion sentence must describe the full user outcome. For example: the
session is not complete when jobs become terminal; it is complete only after
outputs are validated, the named report passes its required reviews, the
requested email is sent, and notification evidence is recorded.

When the final artifact is a substantial report for the user, internal completion
normally hands it to `awaiting human review`; it does not imply acceptance.
Keep machine-readable `session_status` as `in_progress` and the report release
held until the user accepts, supersedes, or closes it. Distinguish PDF delivery,
blocker escalation, completion notification, and Git/source publication even
when one authorized email performs more than one purpose.

Keep the same end-to-end items in the harness todo list. After compaction or
recovery, reconcile that list against the durable contract before continuing.
The database or UI history is useful diagnostic evidence but is not the
recovery authority.

## Permission and access preflight

OpenCode asks before a tool touches a local path outside the project directory;
see [OpenCode](../../../docs/clients/opencode.md) for permission semantics. Before leaving a
session unattended:

1. Record every required local read root and write root in the brief. Keep
   shared checkouts read-only and name the isolated writable worktree.
2. Confirm the project `external_directory` allowlist covers those roots and no
   broader parent. Unknown external paths must remain `ask`.
3. Use the build agent after plan approval. Do not expect a plan agent to gain
   edit access from an external-directory grant.
4. From the parent, perform one harmless read in each external root and a
   non-mutating writability check such as `test -w` in each required write root.
5. Keep local temporary files under `/tmp/opencode/`. Do not invent another
   local temp root during unattended monitoring.

OpenCode V2 reloads configuration changes; verify the effective rules with a
fresh session before relying on changed permissions. If a service restart is
needed, let any active delegated call return or reach its bounded deadline,
checkpoint state and restart one parent at a time. Resume explicitly and
reconcile remote status; scheduler and grid jobs continue while the client is
stopped.

Do not use `--auto` for unattended work: it approves every request that
is not explicitly denied, not just the intended directories.

Use narrow allow rules for covered routine work; neither a rule nor a client
autoaccept setting enlarges the user's authorization. For an uncovered prompt,
return the exact path, operation and missing authority to the user (or the
agreed relay), then verify the intended worker resumed. A programmatic job
monitor does not answer permission prompts. Worker `idle/done` is not overall
closure. Apply the bounded-recovery policy in
[consequential actions](../../session-coordination/references/consequential-actions.md)
without manufacturing new approvals for already-covered technical corrections.

## Monitor selection

Preserve an existing authorized programmatic monitor and attach `monitor_wait`;
otherwise create the reviewed programmatic monitor described below. Delegate
polling only when the monitor scripts cannot run, and record that fallback in
`STATE.md`. Model delegation remains appropriate for bounded interpretation or
validation, not a file-waiting loop.

A delegated fallback is read-only and must name exact jobs, owner, endpoint,
deadline, terminal states, allowed validation and logs, forbidden job or source
actions, returned evidence, and handback condition. It does not transfer the
parent objective, report, interpretation, or notification authority. Run it
from the project checkout and follow [remote work](remote-work.md).

## Programmatic job monitors

Use `scripts/job_monitor.py` for durable polling of PanDA tasks, Slurm
arrays, and session dependencies. The monitor is read-only with respect to the
external system: it may query status and write local evidence, but it must not
submit, retry, cancel, delete, authenticate, renew credentials, inject a harness
prompt, or send mail.

Each monitor has a reviewed JSON specification in the owning session and writes
runtime state under that session's ignored `monitor/` directory:

- `latest.json`: atomic normalized snapshot with an expiry timestamp.
- `snapshots.jsonl`: append-only observation history.
- `result.json`: terminal result or terminal monitor failure.
- `monitor.lock`: exclusive process lock preventing duplicate pollers.

Run one probe before starting a watch:

```bash
python3 scripts/job_monitor.py validate-spec --spec SESSION/monitor-spec.json
python3 scripts/job_monitor.py probe --spec SESSION/monitor-spec.json
python3 scripts/job_monitor.py start --spec SESSION/monitor-spec.json
python3 scripts/job_monitor.py status --spec SESSION/monitor-spec.json
```

`start` uses a transient `systemd --user` unit named `agent-monitor-*` so the
poller survives harness and terminal exits. A valid snapshot is authoritative
only until its `expires_at` value. A missing or expired lease is `stale`, not a
successful or terminal external task. Recover with `start`; the append-only
history remains in place and the monitor resumes from a fresh observation.

Normalized outcomes include `active`, `ready`, `topology_stable`,
`terminal_clean`, `terminal_with_failures`, `failure_attention`,
`invariant_violation`, `transport_error`, and `lease_expired`. The `status`
command reports an absent or expired nonterminal snapshot as `stale`.
The PanDA adapter distinguishes build, payload, and merge jobs, treats merging
as active work, detects truncated job responses, and fails closed on owner,
scope, retry, or payload-count drift. The Slurm adapter merges `sacct` history
with live `squeue` state, records per-index exit evidence, and fails closed when
an expected terminal array index is absent. Dependency monitoring reads only
machine-readable handoff markers and records readiness. External monitor
processes never prompt or wake a harness; the separate parent-owned wait tool
returns their durable evidence.

### Parent wait contract

Create a reviewed wait contract from `wait-contract.template.json` in
the owning session. It binds the parent to exact monitor specifications, a
fail-fast policy, a finite wait, post-handback authority, the complete outcome,
and optional notification authorization. Paths are project-relative and their
content hashes are recorded when the wait registers.

The default `fail_fast_all` policy returns success only after every monitor is
`terminal_clean`, `ready`, or `topology_stable`. It immediately returns the
first failure, attention, invariant violation, stale or absent monitor,
transport exhaustion, spec drift, or lease expiry. This is a handback, not
permission to repair the external task.

The parent owns the end-to-end obligation and notification authorization. The
wait coordinator owns observation and same-turn handback. The detached notifier
performs only the exact authorized delivery operation. After client loss, the
explicitly selected recovery owner reconciles orphaned or uncertain delivery.

After validating and probing the monitor specs, call the `monitor_wait`
OpenCode tool once with the contract path (Claude Code: the
background command above). The wait:

1. Atomically registers the calling session, message, contract hash, and spec
   hashes before inspecting terminal files.
2. Adopts matching live units and starts only missing units through the normal
   monitor start path.
3. Starts a detached local notifier and blocks the current tool call while
   reading monitor files. No model call occurs during this wait.
4. Returns normalized evidence to the same parent turn and marks it
   `delivered_to_tool`.

Runtime state lives under the contract's owning session at
`monitor/waits/<event-id>/`:

- `registration.json`: immutable caller, contract, and monitor identity.
- `state.json`: observation and delivery state with a transition history.
- `result.json`: atomic fail-fast group handback.
- `notification.json`: held, claimed, sent, or failed notification evidence. A
  `notifying` delivery state with only a claimed record means the external
  outcome is uncertain.
- `unit.json`: detached notifier unit metadata.

Observation progresses from `registered` to `waiting` to `completed`. Delivery
progresses independently through `pending`, `delivered_to_tool`, `orphaned`,
`notifying`, `notified`, `notification_failed`, `notification_unknown`, and
`acknowledged` as applicable. The CLI command `notification-unknown` records the
`notification_unknown` state. Operations are idempotent and reject identity
drift.

### Client loss and notification

The detached notifier uses the registered owner process only as a liveness
signal. If that process exits or the tool is interrupted, it marks the wait
`orphaned`, continues reading the already detached monitors, and writes one
durable completion. It never invokes the client, sends a prompt, or starts a
model.

Email is disabled by default. An exact command array and destination must be
authorized in the wait contract. The notifier claims one wrapper attempt before
running the command and never retries an ambiguous claim. This prevents an
automatic duplicate command but cannot guarantee exactly-once external delivery
if the process dies across the side effect. A durable `notifying` state then
requires the operator to inspect the transport, mark `notification-unknown`,
and acknowledge it. If no notification is authorized, the durable orphaned
result remains queued for startup recovery.

Inspect or acknowledge a known event without running a model:

```bash
python3 scripts/monitor_wait.py status \
  --contract SESSION/wait-contract.json --event-id EVENT
python3 scripts/monitor_wait.py notification-unknown \
  --contract SESSION/wait-contract.json --event-id EVENT
python3 scripts/monitor_wait.py ack \
  --contract SESSION/wait-contract.json --event-id EVENT
```

Use `notification-unknown` only after confirming the notifier unit is no longer
active and reconciling the external transport. Acknowledgement records
consumption; it does not validate external outputs or complete the parent
objective.

A normal or recovered handback authorizes only read-only validation and the
downstream actions already recorded in the wait contract and owning session.
Repair, retry, resubmission, cancellation, changed notification, or expanded
scope requires a new explicit authorization and ownership checkpoint. Recovery
must restore or explicitly reassign parent ownership before acknowledging the
event, then update `STATE.md` when the queue is consumed.

### Handoff marker

An owned session writes `HANDOFF.json` atomically at coherent checkpoints. The
marker uses schema version 1 and contains:

```json
{
  "schema_version": 1,
  "session": "sessions/YYYY-MM-DD-task",
  "session_status": "in_progress",
  "updated": "2026-08-20T00:00:00+00:00",
  "owner_session_id": "ses_...",
  "checkpoint": "short factual checkpoint",
  "next_safe_action": "bounded next action",
  "releases": {
    "report": {
      "status": "held",
      "reason": "not yet ready"
    }
  }
}
```

Valid `session_status` values are `in_progress`, `blocked`, `paused`,
`complete`, and `failed`. A release is ready only when its status is
`released`; absence, `held`, or malformed content remains pending. A dependency
spec may instead require a terminal session status. The Markdown `STATE.md`
remains the human-readable source; update the JSON marker at the same coherent
checkpoint, never as a speculative promise.

Map Markdown `in progress` and `awaiting human review` to `in_progress`; map
`blocked`, `paused`, `complete`, and `failed` directly. `not started` has no
handoff marker. During human review, keep the report release held.

### Migration rule

Do not stop an existing watcher until the replacement monitor has passed spec
validation, produced a valid probe snapshot for the same task, and been started
successfully. Preserve legacy evidence. Record the replacement unit, spec, last
legacy observation, and migration timestamp in `STATE.md`. Monitor migration
does not authorize any external job action.

## Terminal handling

Treat scheduler completion as a trigger for validation, not proof that the
scientific or production result is usable.

- On success, verify the predeclared file, event, checksum, schema,
  normalization, provenance, and storage gates before downstream analysis.
- On failure, inspect only relevant status and logs, record the concrete cause,
  and stop. Monitoring authorization alone does not authorize a repair or
  resubmission.
- On partial or mixed completion, preserve successful evidence and identify the
  smallest explicit decision needed for the remaining work.
- Update the owning state and any canonical processing ledger at each terminal
  batch, failure, resubmission, or monitor handback.

## Compaction and recovery

After automatic compaction, interruption, or a new owner taking over:

1. Re-read the owning `BRIEF.md`, `STATE.md`, processing ledger, and report
   contract before querying jobs.
2. Compare their job identifiers and timestamps with current read-only status.
3. Reconstruct todos for monitoring, validation, analysis, report production,
   required reviews, PDF delivery, human review, notification, and final state
   publication.
4. Preserve prior failures and superseded job identifiers in the journal; do
   not silently replace them with the latest attempt.
5. Continue only when the current authorization still covers the next action.

Never mark a session complete merely because a delegated monitor returned,
jobs left the queue, a PDF compiled, or an email command exited successfully.
Use the full completion contract.

## Completion evidence

Before setting `Status: complete`, record:

- final job/task states and terminal validation results;
- final report source and consultation artifact paths;
- required numerical, physics, copy, build, and visual reviews;
- human-review status;
- delivery, blocker-escalation, and completion-notification status, destination,
  timestamp, and non-secret transport result;
- unresolved limitations and the exact publication state;
- the final `RESULT.md` outcome and any remaining human decision.

Do not record message bodies, credentials, tokens, or private mail
configuration. A destination, timestamp, attachment name, and successful local
transport result are sufficient notification evidence.
