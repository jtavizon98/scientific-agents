---
name: render-review
description: Check a rendered PDF report or plotbook mechanically before visual review, then prepare a bounded visual-review request. Use before sending any composed PDF to a reviewer or reader, and when revising pages that already passed review.
---

# Render review

Read [the procedure](references/workflow.md). The checker is
`scripts/render_gate.py` in this skill; run it with the project's Python
environment. It needs Python 3.10 or newer, Pillow, and the MuPDF and Poppler
command-line tools; the full list is under
[dependencies](references/workflow.md#dependencies-and-policy-tuning). Your own
document toolchain (for example TeX) builds the PDF and is not a gate
dependency.

1. Build the exact PDF the reader will receive. Keep its TeX log and, with
   citations, the Biber log.
2. Run `gate` with every input that applies: printed-value manifest, page map
   and plan, previous manifest for reuse. Record in an applicability contract
   why any check does not apply. A missing input leaves its check
   `not_assessed`; it never passes. For slides and posters add
   `--profile slides`.
3. Fix each `blocked` finding in the source that owns it, rebuild and rerun.
   A waiver needs an approval line from the named `--approver` in the
   session's `STATE.md`.
4. Send visual review only from a `ready_for_review` result, with the reading
   tasks, reference rasters and the pages the diff marks for review. The
   reviewer must confirm it can see the pixels; without them the pages are
   not assessed. The protocol for the request and the reading tasks is in
   [visual review](references/visual-review.md).

A passing gate says nothing about whether the reader can do the reading tasks
or whether the numbers are scientifically right. Those need their own review.
