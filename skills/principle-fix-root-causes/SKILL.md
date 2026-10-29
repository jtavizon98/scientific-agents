---
name: principle-fix-root-causes
description: Apply when debugging a failure or chasing a discrepancy between two results. Trace the symptom back to the first place something went wrong and fix it there.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/principle-fix-root-causes/SKILL.md
  adapted-for: scientific work
---

# Fix root causes

Fix the fault, not the place where it surfaced. The symptom is where a wrong state became visible: a yield that disagrees, a crash in a later stage, a histogram with an empty bin. The root cause is the first place the processing did something it should not, or failed to handle a state it should handle.

**Why:** A symptom fix hides the evidence and leaves the fault free to surface elsewhere. A correction factor that makes two numbers agree without a named cause also makes every later comparison less trustworthy.

- **Reproduce first,** yourself, on the smallest input that shows it: one sample, one run, one event when you can find it. Job submission and other gated actions keep their gates.
- **Ask "why" at each step** until the answer is a wrong decision in the code or configuration, not a consequence of an earlier one.
- **Instrument when stuck.** Read the actual value at each stage, the actual configuration that ran and the actual error. Do not guess.
- **Ask whether the triggering state is legitimate.** If an event, object or file may legitimately be in that state, the code that broke on it is the cause. If it should never exist, a guard where it broke hides the bug: find what produced it. Clamped values, swallowed errors, dropped events and silent defaults are the usual hiding places.
- **Suspect stored state** when something fails only on a rerun: caches, intermediate files, lock files, an old output picked up by a glob.
- **Fix the pattern, not the instance.** Find every stage, sample or configuration with the same fault and fix them all.
- **Leave a signal.** If the deciding fact took a deep dig to find, propose the cheap check that would have shown it at once, such as a cutflow line, an assertion or a logged count.

If two fixes on the same assumption fail, stop and [attack the premise](../principle-attack-the-premise/SKILL.md).
