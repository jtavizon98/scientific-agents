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
   re-cut.
2. Write the storyline: audience, slot, the one question, the one-sentence
   take-away, one line per frame with its claim as the title and a time mark,
   the backup frames and the questions they answer, and the source of every
   figure and number.
3. Get the presenter's confirmation before drawing slides. Record choices made
   without them as agent defaults in the storyline.

## Build

- Start from the template: metropolis, 16:9, the Catppuccin palette, the
  question frame, sections, take-away, references, questions frame, backup
  appendix.
- The frame title states the claim; one idea per frame; `\pause` only where
  the argument's order needs it; sources cited on the slide.
- Figures are the plotbook or report files as they are; the talk adds no claim
  the written work does not support.
- Every content frame gets a `\note{}` with what to say, what to point at and
  the time mark. Build the audience PDF and the notes PDF from one source.

## Check and deliver

- Render gate with `--profile slides`
  ([render-review](../render-review/SKILL.md)); fix blocking findings in the
  source.
- Visual review of selected frames as rasters through an economy
  image-capable route; copy review of storyline and notes for a talk others
  will judge.
- A [teach](../teach/SKILL.md) pass on frames the presenter did not write.
- Export the `.pptx` when the room needs PowerPoint. Deliver the PDFs to the
  review inbox as awaiting review; publishing to the audience is the
  presenter's step.
