# Remote execution and interruption

Before execution establish the host, source revision, environment, inputs,
resource limits, output location and success/failure criteria. Distinguish the
writing checkout from a deployed execution copy. Inspect divergence before
updating either; do not overwrite remote changes to make deployment convenient.

## SSH control masters

Before remote work, probe the selected SSH alias non-interactively with
`BatchMode`. A configured OpenSSH control master may provide authenticated
access to the remote host; if it has expired, ask the user to establish it with
one interactive login. Never request, receive or store a password or a
certificate passphrase.

Whenever remote work uses a shared SSH alias or control master:

1. Run one bounded SSH command at a time through an alias; never parallelize
   calls that share a control master.
2. Combine related read-only checks when that avoids unnecessary channels, and
   do not leave diagnostic SSH commands running in the background.
3. After a timeout, broken pipe, multiplexing error or unexpected disconnect,
   stop issuing calls and inspect the master once.
4. Never terminate, replace or recreate the user's control master as an
   incidental repair step.
5. If a `BatchMode` probe fails for lack of authentication, ask the user to
   establish one interactive login. Do not repeatedly probe or request
   credentials.
6. Remote process management must name the exact target process; do not use
   broad process-kill patterns that could affect the SSH master or unrelated
   agents.

Harness process recovery is separate from SSH control-master maintenance. A
harness incident never authorizes changing the shared SSH transport.

## Remote checkouts and execution

A checkout reached through SSH is a deployment or validation copy unless the
project designates that host as the writing client. Mounted remote filesystems
(SSHFS and similar) are never editing locations. With an authenticated master,
the agent may inspect remote state and run commands the current task requires.
Before updating a remote checkout, inspect its branch and worktree, then use
`git pull --ff-only`; do not overwrite remote changes or edit source through SSH
or a mount.

Bounded validation may run on a login host. Scheduler or grid submission,
cancellation, mount changes, deletion and other consequential remote operations
require explicit user intent
([consequential actions](../../session-coordination/references/consequential-actions.md)).
Keep unbounded analysis work inside the scheduler.

Never search a mounted remote tree recursively as part of local discovery. A
failed mount can hang filesystem calls. Use narrowly scoped explicit paths, and
prefer existing text extractions over large binary files.

Prefer runtime evidence over speculation when debugging a remote run. Add
focused logging when needed and, with an authenticated master, run bounded
diagnostics and inspect status or text logs over SSH. Use the matching narrowly
scoped mount path when local access helps with plots or other artifacts.

## Scheduler jobs

For a Slurm or other scheduler job, retain its submitted identity, command/config
and input/source identities. Submission, cancellation and replacement need task
authorization. A successful submit command establishes submission, not completion.
Check output completeness and scientific validation separately from scheduler state.

Long waits should use a programmatic monitor with a bounded timeout and durable
state. Define terminal success, terminal failure, unavailable transport and stale
evidence separately. Do not keep a model alive to poll status. After interruption,
reconcile the existing job before submitting a duplicate. The monitor and wait
scripts are described in [long-running jobs](long-running-jobs.md).
