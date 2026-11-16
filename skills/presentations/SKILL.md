---
name: presentations
description: Plan, build and review talks and posters (Beamer slides, backup slides, a rehearsal pack, a PowerPoint copy) from a study, a thesis, a report or someone else's paper. Use for a defence, colloquium, seminar, journal club, group-meeting update or poster, and for re-cutting an existing deck for another audience or time slot.
---

# Presentations

A talk is an argument the audience hears once, in order, from the person who
presents it. That person judges a deck by looking at it and learns whether
they can defend it by giving the talk aloud, so the agent shows a rendered
skeleton first, polishes second, and prepares the rehearsal. The full
procedure is in [references/deck-production.md](references/deck-production.md);
the Beamer deck and poster templates are in
[references/template/](references/template/README.md); the PowerPoint export
is `scripts/export_pptx.py`.

## Storyline and skeleton

1. Read the source material: the accepted report, `RESULT.md` and plotbook for
   your own work, the full paper for someone else's, the existing deck for a
   re-cut, and what the person who asked for the talk said they want. List
   the aids the written work already has: figures, diagrams, tables, colour
   keys and navigation strips (a strip of the processing chain with the
   current step highlighted).
2. Write the storyline with every field of the
   [storyline contract](references/deck-production.md#the-storyline-contract):
   the brief quoted, one line per frame with its claim as the title, a frame
   count that fits the slot, the working terms kept off the slides, and the
   source of every figure and number.
3. Build the [skeleton](references/deck-production.md#the-skeleton) in the
   first session: every main frame with its claim and a placeholder for its
   figure. Check it against the brief, then get the presenter's confirmation
   on the rendered pages before polishing. Record choices made without them
   as agent defaults in the storyline.

## Build

- Copy `references/template/` into the deck's working folder, set author,
  institute and `\addbibresource` (template README), and keep its frame
  structure (deck-production, Structure). The presenter gets the source and
  its build command with the first draft; their own edits are kept word for
  word ([the presenter's source](references/deck-production.md#the-presenters-source)).
- The frame title states the claim; one idea per frame in the audience's
  words; at most 120 words set on a main frame; `\pause` only where the
  argument's order needs it.
- Figures are the plotbook or report files as they are, never cropped of an
  axis. For a talk from your own study, diagrams and navigation strips are
  the study's asset files, input with the same number macros, never redrawn
  ([deck-production](references/deck-production.md#diagrams-and-navigation)).
  Every number is generated from the artifact that owns it. The talk adds no
  claim the written work does not support.
- A structural change after the confirmation is asked on its own; wording,
  naming and layout are agent defaults.

## Check, rehearse and deliver

- Every build: the presenter's request asserts and the render gate with
  `--profile slides` ([render-review](../render-review/SKILL.md)); fix
  blocking findings in the source.
- Claims review at each change of source. Independent visual review at three
  milestones (the skeleton, the draft that goes to the person named in the
  brief, the final), to the standard in deck-production (Build and review,
  step 4). Drafts in between are recorded as checked by the author only. Copy
  review for a talk others will judge.
- Write the [rehearsal pack](references/deck-production.md#the-rehearsal-pack)
  with the first full draft: points to hit per frame, terms to define,
  expected questions, and the coach's instructions. A timed rehearsal the day
  before, and its findings back into the deck.
- Export the `.pptx` when the storyline lists it. Deliver to the user's review
  inbox, if the project has one, as awaiting review; publishing to the
  audience is the presenter's step.
- On the day of the talk apply late requests directly and write the closing
  record afterwards
  ([the day of the talk](references/deck-production.md#the-day-of-the-talk)).
