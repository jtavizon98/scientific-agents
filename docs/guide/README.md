# Working with agents in a research project

This handbook is for researchers who can use Git and write scientific code but
are new to coordinating agents. It explains how to keep the scientific question,
source evidence and produced artifacts connected. The first extraction covers
source handling and coordination; complete code/report examples are in progress.

## Start from a result you can check

Give the agent a question, intended use and acceptance evidence. For a small bug,
that may be a failing example and a corrected output. For an analysis comparison,
name the populations, definitions, inputs and uncertainty convention before
choosing plots. Settle material decisions before implementation; routine local
changes should not acquire a new planning bureaucracy.

Distinguish three kinds of evidence. Documentation explains intended methods.
Code shows an implementation at a revision. Runtime artifacts show what executed
with particular inputs. Disagreement between them is a finding to investigate,
not a reason to select whichever source supports the desired answer.

## Build a source trail while investigating

Use [source discovery](../../skills/source-discovery/SKILL.md) for bounded questions.
If a source needs a logged-in browser, send that question to a GUI-capable session
and preserve the exact edition and pinpoint in its handoff. A summary without
source identity is hard to verify after the original session ends.

Maintain [one source library](../../skills/source-library/SKILL.md) across reports.
Correct metadata once in its owning entry, cite passages next to claims, and
preserve historical evidence identities. Linked citations help the reader travel
from a claim to the bibliography; backreferences show where a source was used.
Neither replaces the passage locator inside the source.

## Make scientific code readable as a procedure

Use the scientific-coding skill to expose ordered transformations, their reasons,
invariants and checks. Keep each formula and scientific definition in one owner.
Use an independent small calculation to validate a meaningful invariant rather
than a test that simply repeats the implementation. Retain failures and state
the input/mode limits of a successful check.

## Review the actual artifact

Figures answer reader questions, not just requests to plot every available array.
State the comparison, units, normalization and uncertainty treatment. Design the
figure and the composed page together: legibility at full-screen size is not
evidence of readability after placement in a report.

The [plot-evidence workflow](../../skills/plotting-integration/references/plot-evidence.md) separates numerical
checks, mechanical layout checks, inventories and visual reading tasks. Review
prose/source support separately from appearance. Keep the result under human
review until the domain owner accepts it; a model's approval is not that decision.

## Continue work without losing ownership

Use [session coordination](../../skills/session-coordination/SKILL.md) when a task spans
GUI and terminal sessions, clients or machines. One writer owns each boundary;
the receiving session gets exact artifact identities and unresolved questions.
Herdr can make sessions easier to manage, but the durable handoff is what allows
recovery when a pane or client disappears.

Record what was delivered, what notification succeeded and what was accepted.
For [remote work](../../skills/long-job-continuation/SKILL.md), keep job identity and verify its
outputs before calling the scientific task complete. Resume by reconciling
current reality with the record, not by replaying the last command blindly.
