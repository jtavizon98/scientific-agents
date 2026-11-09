---
name: session-coordination
description: Coordinate work across agent sessions, GUI and terminal clients or machines with one writer per boundary and durable BRIEF/STATE/RESULT records. Use when delegating, handing off, resuming after an interruption, taking a consequential action, changing a workflow or policy, or running a GUI session beside a terminal one.
---

# Session coordination

Core rules, then one reference per situation. Templates for durable session
records are in `references/templates/`.

1. Name the owner, repository, branch, working directory, host and native
   session ID before splitting work. Give every writer its own files or
   worktree, and keep one integrator.
2. Brief each delegate with the question, owned paths, evidence, constraints,
   expected outputs and stopping condition.
3. Record substantial, delegated or interruptible work in `BRIEF.md`,
   `STATE.md` and `RESULT.md`. Routine local work needs none of them. Fill
   the `STATE.md` header with the template's values, put renders and builds
   in the session's ignored `build/` folder, and name each deliverable in
   `RESULT.md`: unnamed build output of a closed session is offered for
   deletion.
4. At handoff, name the exact artifact and what was checked. Keep file creation,
   delivery, notification and human acceptance as separate facts. A session
   that replaces earlier ones names them under `Supersedes` in its `BRIEF.md`;
   a push request accepts workflow work, not physics
   ([acceptance](references/consequential-actions.md#acceptance)).
5. Decide, record, report: proceed on reversible work and on defensible
   scientific defaults, record each default in `STATE.md`, and keep dependent
   results awaiting review ([consequential actions](references/consequential-actions.md)).
6. After an interruption, compare the records with Git status, running
   processes and job state before resuming. Never resume one native session
   from two clients at once.

## Which reference

- Splitting work across GUI, terminal or machines: [workflow](references/workflow.md).
- Delegating to another agent or model: [delegation](references/delegation.md).
- Deleting, pushing, submitting, delivering, mounting or renewing anything:
  [consequential actions](references/consequential-actions.md).
- Starting a writing task, updating a checkout, committing or handing code
  over: [Git coordination](references/git-coordination.md).
- Changing a policy, workflow, skill or its enforcing scripts:
  [workflow changes](references/workflow-changes.md).
- Returning after a crash, disconnect or reboot: [recovery](references/recovery.md).

For unattended work see the sibling skill [unblocker](../unblocker/SKILL.md).
Herdr is optional; see the [Herdr guide](https://github.com/jtavizon98/scientific-agents/blob/main/docs/clients/herdr.md).

## User-only steps

A step only the user can perform (a bot check or CAPTCHA, a password,
passphrase or 2FA prompt, an interactive login, a credential renewal) blocks
only the work that needs it. Never perform it, wait it out or script it, and
never ask for the secret. Tell the user at once: the exact URL or command and
where to run it, such as your own browser pane so its cookie reaches you, or a
named terminal and host. Record the request and the work it blocks under
"Blockers and gaps" in `STATE.md` (and under "Open questions to the user" when
an [unblocker](../unblocker/SKILL.md) relays them), carry on with the
independent work, and resume the blocked step when the user confirms. You
cannot receive that confirmation mid-turn: finish the independent work, then
end the turn with the request still open; with nothing independent left, end
it at once. A delegate reports the request in its handback.
