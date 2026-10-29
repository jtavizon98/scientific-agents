---
name: principle-explain-the-number
description: Apply before you measure, and before you trust, report or act on a measured number such as a yield, an efficiency, a ratio or a timing.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/principle-explain-the-number/SKILL.md
  adapted-for: scientific work
---

# Explain the number

- **Write the decision before you run.** Name the result that would change a decision, and the noise floor. If the run-to-run or statistical spread is larger than the effect, stop and get more events or runs.
- **Ask "why not double?"** Name what bounds the number: the acceptance, a trigger or selection requirement, a weight, a core, the disk, the queue. Get it from the cutflow, a profile or the job's own counters, then map it to the code. A guess from reading the config is not a limiter. If you cannot say why the number is not twice as large or small, you do not know what you measured.
- **Rule out that it measured something else.** The usual suspects are the wrong sample or period, missing or doubled weights, a different normalization, different binning or range, mixed units, a stage that was skipped or served from cache, a job that failed partway, and a piece too small to matter end to end.
- **Keep the evidence with the number.** Put the sample, the weights used, the event count, the spread and the limiter next to the number in the notes, the table or the plot metadata.

A ratio between two processings of the same events should be near one for a stated reason. If it is not, find the stage where the two first differ before explaining the physics. When a mismatch persists through a stage-by-stage chain, the stage where it appears first owns it.

You skipped this when a run started without the result that would change a decision, or when a number has no count, no spread and no named limiter.

Distinct from [Prove it on the real artifact](../principle-prove-it-on-the-real-artifact/SKILL.md), which checks that an output is real. For the code behind a number, see [scientific-coding](../scientific-coding/SKILL.md).
