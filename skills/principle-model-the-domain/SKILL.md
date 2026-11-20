---
name: principle-model-the-domain
description: Apply when writing stateful logic, or when code branches a lot or repeats an assumption about the shape of the data across files.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/aaeb0ea/pstack/skills/principle-model-the-domain/SKILL.md
  adapted-for: scientific work
---

# Model the domain

Encode the domain in a data structure instead of scattering it across conditionals. The right structure makes invalid states unrepresentable and deletes branches.

Reach for:

- a **type that carries what belongs together**: a histogram whose underflow and overflow bins carry their variance like every other bin, instead of side arrays that every function must keep the same length;
- an **enum or union for exclusive modes**: one `PlotMode` with the allowed combinations, not three boolean flags validated by hand in each caller;
- a **result type with a validity mask** instead of NaN or a sentinel value that each caller must remember to test;
- a **map or registry** instead of the same `if name == ...` chain in several files;
- a **state machine** instead of scattered flags or phase checks.

Do not force it. Keep plain code when the shape is clear, local and unlikely to grow, and distrust an abstraction that adds indirection without removing branches or invalid states.

You skipped this when a change adds one more branch to an if/else chain, when a second variable must stay in sync with the first, or when two files repeat the same assumption about array shapes or flag combinations.

Related: [codebase-design](../codebase-design/SKILL.md), for where the new type's module and its seam go; [scientific-coding](../scientific-coding/SKILL.md), for the one owner of each convention.
