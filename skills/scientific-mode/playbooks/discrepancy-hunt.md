# Discrepancy hunt

Two results that should agree do not: a reproduction against its reference, two
processings, two software versions, or a per-event audit that finds events on
one side only. The goal is the cause, named and shown, not agreement.

1. State the discrepancy as numbers: which quantity, which inputs, how large,
   and how large a difference would be expected (statistical, from known
   changes). If it is within expectation, say so and go
   to step 8 ([explain the number](../../principle-explain-the-number/SKILL.md)).
2. Reproduce it yourself on the smallest input that shows it: one sample, one
   run, one event where possible. Keep the reproduction as a script
   ([build the lever](../../principle-build-the-lever/SKILL.md)).
3. List the candidate causes, then rule them out by splitting the problem: by
   stage of the cutflow, by sample, by object, by configuration difference.
   Take the split that removes the most candidates, read the actual values,
   and eliminate. Do not guess between candidates; instrument.
4. When a hypothesis is refuted, revert what it motivated. When two fixes on
   the same assumption fail, test the assumption
   ([attack the premise](../../principle-attack-the-premise/SKILL.md)).
5. Trace the surviving cause to the first place the processing went wrong and
   fix it there, everywhere the same fault occurs
   ([fix root causes](../../principle-fix-root-causes/SKILL.md)). If the
   difference is a legitimate choice rather than a fault, record the choice
   and its effect instead of changing either side; when that judgment is
   yours, record it as an agent default
   ([decide, record, report](../../session-coordination/references/consequential-actions.md#decide-record-report)).
6. Show it on the real inputs: the original comparison now agrees, or the
   remaining difference is explained number by number
   ([prove it on the real artifact](../../principle-prove-it-on-the-real-artifact/SKILL.md)).
7. Propose the cheap check that would have shown the cause at once, such as a
   cutflow line, an assertion or a logged count.
8. Record in `RESULT.md` the discrepancy, the cause, the fix or recorded
   choice, the before and after numbers and the reproduction script, or, for
   a difference within expectation, the calculation of the expected size. If the
   conclusion depends on physics or numerical judgment, review it with a
   [council](../../council/SKILL.md).
