# Design it twice

Use this to explore alternative interfaces for one chosen deepening candidate.
Your first design is unlikely to be the best (Ousterhout). Uses the vocabulary
of [codebase-design](../SKILL.md) and the dependency categories in
[deepening](deepening.md).

## Process

1. **Frame the problem space** for the user before spawning anything:
   - the constraints any new interface must meet, including the past failures it
     must make impossible;
   - the dependencies and their categories;
   - a rough code sketch that makes the constraints concrete. It is not a
     proposal.

   Show it, then go straight to step 2. The user reads while the agents work.

2. **Spawn three or more fresh-context agents in parallel**, each producing a
   radically different interface. Each gets a separate technical brief: file
   paths, how the pieces couple, the dependency category, what sits behind the
   seam, the project's own domain vocabulary and invariants (its `AGENTS.md` and
   decision records), and one design constraint:
   - minimize the interface: one to three entry points, maximum leverage each;
   - maximize flexibility: many use cases and extension;
   - optimize the most common caller: the default case is trivial;
   - if a cross-seam dependency exists, design around a port and adapters.

   Each returns: the interface (types, parameters, invariants, ordering, error
   modes); a usage example from a real caller; what the implementation hides;
   the dependency strategy and adapters; and where leverage is high or thin.
   If no agent tool is available, produce the designs yourself one at a time,
   starting each from the brief and not from the previous design.

3. **Present and compare** in prose, one design at a time. Compare on depth,
   locality and seam placement, and on one test: which design would have made
   the recorded failures impossible to write. Then give your own recommendation,
   or a hybrid if parts combine well. The user wants a strong read, not a menu.
   Confirm the choice with [grilling](../../grilling/SKILL.md) before
   implementing.
