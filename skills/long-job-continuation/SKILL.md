---
name: long-job-continuation
description: Wait for PanDA, Slurm or dependency jobs that outlive the current step without polling tokens or a polling subagent, using a durable monitor, one parent-owned wait and a recorded completion contract. Use when a job is submitted and the parent must resume on its terminal state.
---

# Long-job continuation

Read [long-running jobs](references/long-running-jobs.md) before registering a
wait. For SSH, shared control masters and scheduler rules see
[remote work](references/remote-work.md).

The wait backend is `scripts/monitor_wait.py wait`, which takes
`--harness {opencode,claude,codex}`, `--session-id`, and `--owner-pid`;
`--message-id` is required only for `opencode`. The monitors it waits on are
`scripts/job_monitor.py` specifications (PanDA, Slurm, session dependencies).

- OpenCode: call the `monitor_wait` tool, provided by
  `scripts/opencode-monitor-wait.ts`. Registering that plugin is a separate
  step ([OpenCode](https://github.com/jtavizon98/scientific-agents/blob/main/docs/clients/opencode.md#registering-monitor_wait));
  until the tool appears in the agent's tool list, treat it as unavailable and
  do not start unattended work.
- Claude Code: run one `run_in_background` command with `--harness claude
  --session-id "$CLAUDE_CODE_SESSION_ID" --owner-pid "$CLAUDE_PID"` and a
  `--timeout-seconds` below 7200; the session is re-invoked when it exits. On
  `wait_timeout` with monitors still active, re-arm with a fresh `--event-id`.
  Exact command: [long-running jobs](references/long-running-jobs.md). See
  [Claude Code](https://github.com/jtavizon98/scientific-agents/blob/main/docs/clients/claude-code.md).
- Codex: unverified. Retain existing monitors and use an already-assigned
  capable OpenCode or Claude owner, or hand back the precise continuation gap.
  See [Codex](https://github.com/jtavizon98/scientific-agents/blob/main/docs/clients/codex.md).

Do not claim an unattended callback on an unverified client, invent session
identities, or launch a polling agent merely because this skill was discovered.
Read-only inspection of retained monitor evidence remains available. A new
watcher assignment or integration is separate scope.

1. Record the full user-facing completion contract in the owning `BRIEF.md` and
   current authorization in `STATE.md` (see
   [session coordination](../session-coordination/SKILL.md)).
2. Create a reviewed wait contract from
   [the template](references/wait-contract.template.json); the monitor specs
   it names start from the [examples](references/long-running-jobs.md#programmatic-job-monitors). Use exact
   project-relative monitor-spec paths. Leave notification disabled unless the
   user authorized its exact destination and command.
3. Validate and probe each monitor specification. Do not replace a live monitor
   merely to use this tool.
4. Start the wait once (`monitor_wait` or the Claude background command). Do not
   delegate a polling subagent and do not issue model-driven status checks while
   it runs. The one exception is a recorded, read-only fallback when the monitor
   scripts cannot run (see [monitor selection](references/long-running-jobs.md#monitor-selection)).
5. When the tool returns, treat its result as a handback trigger. Validate
   external outputs and continue only the actions authorized by the wait
   contract and the owning `BRIEF.md` and `STATE.md`.
6. If the owning client process exits, the monitor remains detached. Recovery
   reads the wait state and notification evidence, explicitly restores or
   reassigns ownership, and never starts a model automatically.

The default group policy is fail-fast-all: every monitor must finish cleanly or
be ready, while the first failure, attention, invariant, stale snapshot,
transport exhaustion, absent monitor, or lease expiry returns immediately.

For keeping an executor moving across usage limits and waits see
[unblocker](../unblocker/SKILL.md).
