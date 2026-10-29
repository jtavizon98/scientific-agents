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
   `STATE.md` and `RESULT.md`. Routine local work needs none of them.
4. At handoff, name the exact artifact and what was checked. Keep file creation,
   delivery, notification and human acceptance as separate facts.
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

For unattended work see the sibling skill [unblocker](../unblocker/SKILL.md);
for steps only the user can perform see [wizard](../wizard/SKILL.md). Herdr is
optional; see the [Herdr guide](https://github.com/jtavizon98/scientific-agents/blob/main/docs/clients/herdr.md).
