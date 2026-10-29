---
name: render-review
description: Check a rendered PDF report or plotbook mechanically before visual review, then prepare a bounded visual-review request. Use before sending any composed PDF to a reviewer or reader, and when revising pages that already passed review.
---

# Render review

Read [the procedure](references/workflow.md). The checker is
`scripts/render_gate.py` in this skill; run it with the project's Python
environment. It needs PyMuPDF and the project's TeX tools.

1. Build the exact PDF the reader will receive. Keep its TeX log and, with
   citations, the Biber log.
2. Run `gate` with every input that applies: printed-value manifest, page map
   and plan, previous manifest for reuse. Record in an applicability contract
   why any check does not apply. A missing input leaves its check
   `not_assessed`; it never passes.
3. Fix each `blocked` finding in the source that owns it, rebuild and rerun.
   A waiver needs an approval line from the named `--approver` in the
   session's `STATE.md`.
4. Send visual review only from a `ready_for_review` result, with the reading
   tasks, reference rasters and the pages the diff marks for review. The
   reviewer must confirm it can see the pixels; without them the pages are
   not assessed.

A passing gate says nothing about whether the reader can do the reading tasks
or whether the numbers are scientifically right. Those need their own review.
