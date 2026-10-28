# Reconstruct a trace

Use this mode when asked to audit or reconstruct how an existing implementation
arose, or to produce a replayable rewrite. Do not impose it on ordinary fixes.

Establish the actual starting revision and requested endpoints. Verify ancestry
from Git and retained artifacts; list current upstream drift separately. Do not
invent ancestry from today's upstream head or present an explanatory patch
sequence as the actual historical commit sequence.

Group changes by scientific or engineering purpose. For each group preserve the
base and resulting identity, exact patch or existing commit range, sourced reason,
expected behavior, executed check and observed outcome. Label reconstructed
logical groupings and inferred motives. A reason without contemporaneous support
remains an inference or unknown, even if the current code is easy to explain.

Keep distinct scientific endpoints as distinct branches of the narrative.
Record intentional definition differences and unresolved discrepancies; do not
silently retarget one endpoint to another or attribute a multi-factor comparison
to one cause.

Use focused checks per logical change and fresh framework execution at
behavior-changing milestones. Retain failed attempts and give corrected attempts
new evidence identities. A final successful run does not prove every intermediate
state was executed. Mark unexecuted checkpoints explicitly.

Keep the present implementation readable first. The repository trace connects
it to source decisions and actual diffs; exhaustive attempt history belongs in
linked evidence. Only build a machine-readable concordance or replay automation
when the task's audit/reproduction requirement needs it.
