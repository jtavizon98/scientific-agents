---
name: presentations
description: Plan, build and review talks and posters (Beamer slides, speaker notes, backup slides, a PowerPoint copy) from a study, a thesis, a report or someone else's paper. Use for a defence, colloquium, seminar, journal club, group-meeting update or poster, and for re-cutting an existing deck for another audience or time slot.
---

# Presentations

A talk is an argument the audience hears once, in order, from the person who
presents it. That person must be able to defend every frame, so the agent
settles the storyline with them first and builds the deck second. The full
procedure is in [references/deck-production.md](references/deck-production.md);
the Beamer deck and poster templates are in
[references/template/](references/template/README.md); the PowerPoint export
is `scripts/export_pptx.py`.

## Storyline first

1. Read the source material: the accepted report, `RESULT.md` and plotbook for
   your own work, the full paper for someone else's, the existing deck for a
   re-cut. List the aids the written work already has: figures, diagrams,
   tables, colour keys and navigation strips
   (a strip of the processing chain with the current step highlighted).
2. Write the storyline with every field of the
   [storyline contract](references/deck-production.md#the-storyline-contract):
   one line per frame with its claim as the title and a time mark, and the
   source of every figure and number, and which of the written work's aids the
   deck reuses.
3. Get the presenter's confirmation before drawing slides. Record choices made
   without them as agent defaults in the storyline.

## Build

- Copy `references/template/` into the deck's working folder, set author,
  institute and `\addbibresource` (template README), and keep its frame
  structure (deck-production, Structure).
- The frame title states the claim; one idea per frame; `\pause` only where
  the argument's order needs it; sources cited on the slide.
- Figures are the plotbook or report files as they are. For a talk from your
  own study, diagrams and navigation strips are the study's asset files, input
  with the same number macros, never redrawn
  ([deck-production](references/deck-production.md#diagrams-and-navigation)).
  The talk adds no claim the written work does not support.
- Every content frame gets a `\note{}` with what to say, what to point at and
  the time mark. Build the audience PDF and the notes PDF from one source.

## Check and deliver

- Walk the presenter through every frame they did not draft
  ([teach](../teach/SKILL.md)); if they are away, record it as pending.
- Render gate on the audience PDF with `--profile slides`
  ([render-review](../render-review/SKILL.md)); fix blocking findings in the
  source.
- Visual review of selected frames as rasters through an economy
  image-capable route, to the standard in deck-production (Build and review,
  step 4): the reviewer rejects a frame that looks unfinished, and it is fixed
  in the source and reviewed again. Copy review of storyline and notes for a
  talk others will judge.
- Export the `.pptx` when the storyline lists it. Deliver to the user's review
  inbox, if the project has one, as awaiting review; publishing to the
  audience is the presenter's step.
