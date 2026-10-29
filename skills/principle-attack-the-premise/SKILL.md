---
name: principle-attack-the-premise
description: Apply when two or more fixes that share one assumption have failed the same check.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/principle-attack-the-premise/SKILL.md
  adapted-for: scientific work
---

# Attack the premise

When two or more fixes that share one premise fail the same check, suspect the premise, not the fixes.

**Why:** Each failed fix is evidence against the belief it assumed. A third fix on the same premise spends effort where the evidence says the cause is not.

- **Write the premise down.** It is the one sentence every failed fix assumed, for example "the mismatch comes from the b-tag calibration" or "the two inputs have the same event selection".
- **Test the premise before the next fix.** Find an observation that would come out differently if the premise were false, and make it. Look at how the failures are distributed (which samples, runs, bins or stages), not only how large they are. Keep the check rerunnable as a script.
- **Follow the evidence.** If it contradicts the premise, the cause is elsewhere: look for what the failures share that the premise did not predict. If it confirms the premise, ask the next "why". The earlier fixes may have treated a consequence.
- **Remove the condition instead of compensating for it.** If one sample or bin always lands on the losing side, change what puts it there. A correction factor that patches the symptom leaves the cause in place and must be maintained on every rerun.

**Stop:** do not start the next fix before the premise is written down and tested.

Distinct from a redesign: this questions a fact the current analysis assumes, not its structure. When the premise is a decision others depend on, settle it with [grilling](../grilling/SKILL.md). See also [Explain the number](../principle-explain-the-number/SKILL.md) for ruling out what a failing number measured.
