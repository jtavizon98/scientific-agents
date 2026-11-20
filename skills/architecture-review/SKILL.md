---
name: architecture-review
description: Review a codebase for deepening opportunities: scope by hot spots or a named direction, map the failure record to modules, walk the code with a fresh-context agent, rank verified candidates, then grill the chosen ones. Invoke when the user asks for an architecture review.
disable-model-invocation: true
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/mattpocock/skills/blob/abeeaf9/skills/engineering/improve-codebase-architecture/SKILL.md
  adapted-for: scientific libraries and analysis code
---

# Architecture review

Find refactors that turn shallow modules into deep ones, ranked by evidence.
This is a read-only pass that ends in a decision record, not in edits.

Use the vocabulary and principles of [codebase-design](../codebase-design/SKILL.md)
exactly: module, interface, depth, seam, adapter, leverage, locality, the
deletion test. Do not drift into "component", "service" or "boundary".

The project's own instructions (`AGENTS.md` invariants, the owners named in
[scientific-coding](../scientific-coding/SKILL.md), earlier decision records)
give the domain language and the decisions not to re-litigate. A candidate that
contradicts one is reported only when the friction justifies reopening it, and
is marked as doing so.

## 1. Scope

Decide where to look before looking. Deepening pays off where code keeps
changing.

- If the user named a direction (a module, a subsystem, a pain point), take it.
- Otherwise find hot spots in the history:
  `git log --since=<date> --name-only --format= | sort | uniq -c | sort -rn | head -30`
  and `git log --oneline` for fix commits. Let the files that keep coming up
  pull attention first. If changes are scattered, widen the window.

## 2. Mine the failure record

This step comes before the code walk. The failures that already happened tell
you which modules lack depth.

- Gather: fix commits and their messages, session records and handoffs, review
  and council findings, issue reports, and bugs first seen in a plot or a
  number. Note who found each one; a bug found by external review and not by a
  test points at a missing test at the interface.
- Map each failure to the module where the broken rule should have lived, and
  classify it, for example: one rule implemented several times with the copies
  diverging; silent loss instead of an error; state read from two places; a
  convention (units, flow bins, orientation) left to each caller.
- Keep a table: failure | source | module(s) | class | found by. Mark a
  mapping you inferred as inferred. Do not invent history
  ([fix root causes](../principle-fix-root-causes/SKILL.md)).
- A class that recurs across failures is the strongest lead. Several copies of
  one rule is the usual first finding.

## 3. Walk the code

Spawn a fresh-context agent to walk the scoped code. Brief it with the
[codebase-design](../codebase-design/SKILL.md) path, the scope, the failure
table, and the project's invariants; ask for file:line evidence. If no agent
tool is available, do the walk yourself after clearing your working notes. Let
it explore, noting friction:

- Where does understanding one concept mean bouncing between many small
  modules?
- Where is the interface nearly as complex as the implementation?
- Where were pure functions extracted for testing while the bugs live in how
  they are called, so locality is missing?
- Where do copies of one rule exist, and do they agree? Run them on the same
  input.
- Where do tightly coupled modules leak across a seam?
- Which parts are hard to test through their current interface, or untested?

Apply the deletion test to anything that looks shallow.

## 4. Verify before reporting

Every load-bearing claim gets checked, not recalled: open the file:line; count
copies with a search; run two implementations on the same input to show they
differ; time a suspected cost with a cheap probe. A measurement is cheaper than
asking the user which path matters
([prototype, don't ask](../principle-prototype-dont-ask/SKILL.md),
[explain the number](../principle-explain-the-number/SKILL.md)). Drop or
downgrade what you cannot verify, and say so.

## 5. Report candidates

Reply in the conversation. Write a report per
[report-writing](../report-writing/SKILL.md) only when the user asks or the
list is long; follow [unslop](../unslop/SKILL.md) either way. Do not propose
interfaces yet. For each candidate, ranked by failure evidence and leverage:

- **Files**, with file:line.
- **Problem**: the friction, tied to the failures in step 2.
- **Deepening**, in plain words.
- **Dependency category** (see [deepening](../codebase-design/references/deepening.md)).
- **Tests that move**: which tests go and which interface-level tests replace
  them.
- **Strength**: Strong (verified failures, clear owner), Worth exploring
  (evidence is partial), or Speculative (a hunch).

Then two short lists: modules that **look shallow but pass the deletion test**,
and modules that are **already deep**, so nobody deepens them again. End with
the top recommendation and why. Then ask which candidates to take forward.

## 6. Grill the chosen candidates

Run [grilling](../grilling/SKILL.md) on those the user picks: constraints,
dependencies, the shape of the deepened module, what sits behind the seam, which
tests survive, which numbers must stay bit-identical. Record the outcome in the
project's decision record. A candidate rejected for a load-bearing reason goes
into that record too, so the next review does not suggest it again. For
alternative interfaces, use
[design it twice](../codebase-design/references/design-it-twice.md).

Grilling confirmation is not authorization. Implementation follows the project's
own process, with the replace-don't-layer testing in
[deepening](../codebase-design/references/deepening.md).
