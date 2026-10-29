# GUI, terminal and cross-client sessions

Choose the execution environment for the work, not the window currently visible.
A laptop browser may read a source while a remote terminal runs analysis. The
GUI session returns evidence; it does not implicitly take ownership of the code.

For substantial or interrupted work record the task owner, repository, branch,
working directory, host and native session identity. A pane title is a convenient
label, not a reliable identity. Use [BRIEF](templates/BRIEF.md),
[STATE](templates/STATE.md) and [RESULT](templates/RESULT.md)
when they help recovery; routine local work need not create a session directory.

Give each writer non-overlapping files or its own branch/worktree. Keep one
integration owner. A delegate receives the question, owned paths, evidence,
constraints, expected outputs and stopping condition. A GUI discovery brief
also lists exact source URLs and what remains unread. Browser and computer
tools follow the access rules of the client actually providing them.

At handoff, identify the exact produced artifact and what was checked. Distinguish
file creation, delivery, notification, receiving-session reconciliation and
human acceptance. Inspect current state before resuming or prompting another
session; a previous completion message is not proof that current work stopped.

After interruption compare durable state with Git status, running processes and
job status. Recover the latest evidence before launching replacement work. Do
not resume one native session concurrently from two control surfaces. Reconnect
does not by itself authorize old queued actions.

Related procedures: [delegation](delegation.md), [recovery](recovery.md),
[Git coordination](git-coordination.md) and
[consequential actions](consequential-actions.md).

[Herdr](../../../docs/clients/herdr.md) is an optional control surface for this procedure.
The workflow also works with separate terminals and explicit file handoffs.
