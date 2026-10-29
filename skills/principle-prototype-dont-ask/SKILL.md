---
name: principle-prototype-dont-ask
description: Apply when you are about to ask the human a which-approach question whose answer could be observed by running something cheap.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/poteto-mode/SKILL.md
  adapted-for: scientific work
---

# Prototype, don't ask

Before asking "which approach?", classify the question.

- **Observable:** the answer is a fact a cheap run can show. Render two layouts, count the events passing each cut, time one file through each step, check whether two selections give the same yield. This is not the human's call. Run it and decide from the result.
- **A preference or a scientific direction:** which figure the supervisor will find clearer, which systematic to prioritize, what the thesis argues. No experiment settles it. Take the default best supported by the sources and what is already agreed, record it and keep going ([decide, record, report](../session-coordination/references/consequential-actions.md#decide-record-report)). Ask first only when no default is defensible or the choice changes what the work is for; then ask with the evidence you have, per [grilling](../grilling/SKILL.md).
- **A read-only question:** if the deliverable is a cited answer, answer it from sources. Do not build a sketch.

## How to prototype

1. **Name the decision** the sketch exists to make. No decision, no prototype.
2. **Build it throwaway,** in a scratch directory apart from the real code: the smallest script or page that exercises the question. No tests, no abstractions, no polish.
3. **Put variants side by side,** each labeled, so one look compares them. Try an option the human did not name when it is cheap. Do not stop at the first workable one.
4. **Observe the real thing:** the rendered page, the printed yields, the measured time. The observation is the test.
5. **Report** the variants, the evidence, the trade-offs, your recommendation and the scratch path. Say the prototype is throwaway. Build the real version separately.

## Defaults chosen without the human

When you decide an observable fork, or apply a default because the human is away, record it with its evidence where the session's state lives, in the "Agent defaults (unreviewed)" table, following [decide, record, report](../session-coordination/references/consequential-actions.md#decide-record-report). Say in the report what the human can change and how. A default never covers a consequential action.
