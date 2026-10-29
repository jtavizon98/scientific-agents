---
name: principle-prove-it-on-the-real-artifact
description: Apply when you are about to call work done, and the evidence is a dry run, a proxy or a self-report instead of the produced output.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/principle-prove-it-works/SKILL.md
  adapted-for: scientific work
---

# Prove it on the real artifact

Done means checked on the output that was produced: the built PDF, the produced ntuple or histogram, the merged result. A dry run, a proxy or "it compiles" does not count.

**Why:** Unverified work has unknown correctness. Indirect checks (file timestamps, a zero exit code, a job's own success message, a cached figure) feel cheaper than looking at the output. Acting on a wrong inference costs more than the check.

- **Read the real value.** Open the output file and read the quantity: the event count in the merged file, the number in the built table, the axis in the rendered figure. Do not read a log line about it.
- **Check liveness directly.** A job is running when the scheduler or the process says so now, not because its output directory exists.
- **When a check fails, suspect the observation first.** A stale cache, the wrong file or the wrong build directory fails more often than the analysis does.
- **Script the check when you can.** A script that reruns the same comparison and keeps its output beats an eyeball. Keep it visible to the reader; commit it only when the result must stay auditable, such as a reprocessing or a migration.

For built documents and figures, [render-review](../render-review/SKILL.md) is the mechanical check. For what a number means once it is real, see [Explain the number](../principle-explain-the-number/SKILL.md).
