---
name: session-coordination
description: Coordinate work across agent sessions, GUI and terminal clients or machines with one writer per boundary and durable BRIEF/STATE/RESULT records. Use when delegating, handing off, resuming after an interruption, or running a GUI session beside a terminal one.
---

# Session coordination

Read [the procedure](references/workflow.md). Templates for durable session
records are in `references/templates/`.

1. Name the owner, repository, branch, working directory, host and native
   session ID before splitting work. Give every writer its own files or
   worktree, and keep one integrator.
2. Brief each delegate with the question, owned paths, evidence, constraints,
   expected outputs and stopping condition. A GUI brief also lists exact source
   URLs and what is still unread.
3. Record substantial, delegated or interruptible work in `BRIEF.md`,
   `STATE.md` and `RESULT.md`. Routine local work needs none of them.
4. At handoff, name the exact artifact and what was checked. Keep file creation,
   delivery, notification and human acceptance as separate facts.
5. After an interruption, compare the records with Git status, running
   processes and job state before resuming. Never resume one native session
   from two clients at once.

Herdr is optional; see the [Herdr guide](../../docs/clients/herdr.md).
