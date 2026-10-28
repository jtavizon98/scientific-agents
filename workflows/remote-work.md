# Remote execution and interruption

Before execution establish the host, source revision, environment, inputs,
resource limits, output location and success/failure criteria. Distinguish the
writing checkout from a deployed execution copy. Inspect divergence before
updating either; do not overwrite remote changes to make deployment convenient.

Use a bounded noninteractive SSH probe. If authentication fails, ask the user
to establish an interactive connection; do not request passwords or private keys.
With shared control masters, serialize commands, stop after a transport failure,
and inspect the connection rather than killing or recreating the user's master.
Never recursively search mounted remote trees as part of local discovery.

For a Slurm or other scheduler job, retain its submitted identity, command/config
and input/source identities. Submission, cancellation and replacement need task
authorization. A successful submit command establishes submission, not completion.
Check output completeness and scientific validation separately from scheduler state.

Long waits should use a programmatic monitor with a bounded timeout and durable
state. Define terminal success, terminal failure, unavailable transport and stale
evidence separately. Do not keep a model alive to poll status. After interruption,
reconcile the existing job before submitting a duplicate.

The portable monitor implementation is still being extracted. Until available,
use your project's existing monitor or scheduler commands and report the actual
verification scope. ATLAS/grid-specific procedures belong in the group extension.
