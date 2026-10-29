# Study and comparison

A new study, validation or reproduction, or a comparison between processings,
software versions or a reference result.

1. Name the reader and the question, and say which result would answer it.
2. Recover what is already agreed: decision records, the group's conventions,
   accepted results and the reference to reproduce. Do not reopen them.
3. Write the stage record before any code: authoritative sources, named
   stages, an oracle independent of the code, acceptance evidence and
   non-goals ([scientific-coding](../../scientific-coding/SKILL.md)).
4. Fix the comparison: which processings or references, which quantities,
   binning, normalization and uncertainties, including covariance when both
   sides share events. Record any choice you make without the user as an agent
   default.
5. Build in small stages, each ending in a check against the oracle or an
   independent number. Do not start the next stage on an unchecked one. When a
   check fails and the cause is not obvious, switch to the
   [discrepancy hunt](discrepancy-hunt.md) for it.
6. Explain every number before you interpret it
   ([explain the number](../../principle-explain-the-number/SKILL.md)). When
   two fixes fail the same check, test their shared assumption
   ([attack the premise](../../principle-attack-the-premise/SKILL.md)).
7. Run on the intended inputs at the intended scale; a reduced test sample is
   a prototype, not the result
   ([prove it on the real artifact](../../principle-prove-it-on-the-real-artifact/SKILL.md)).
8. Present the result with the [figures and reports](figures-and-reports.md)
   playbook.
9. Record in `RESULT.md` what was shown, its coverage, the agent defaults it
   depends on and the leftovers. The status stays awaiting human review until
   the user accepts it.
