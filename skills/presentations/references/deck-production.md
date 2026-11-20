# Deck production

The procedure behind the [presentations](../SKILL.md) skill: the storyline
contract and the skeleton, slide rules, the kinds of talk, the presenter's
source, the rehearsal pack, build and review. The [template](template/README.md)
implements the conventions named here.

## The storyline contract

The audience hears a talk once, in order, at the speaker's pace, and cannot
turn back, so settle the argument before polishing any slide. Write the
storyline in the session record:

| Field | Content |
| --- | --- |
| Kind | Own work, re-cut, someone else's paper, group-meeting update or poster |
| Audience | Who listens, what they already know, what they will do with the talk, and whether they are inside the presenter's group or outside it |
| Brief | What the person who asked for the talk or supervises it said they want, quoted, and the date the first polished draft goes to them (at least five working days before the talk) |
| Slot | Length of the talk and of the questions, and the number of main frames it allows |
| Question | The one question the talk answers |
| Take-away | One sentence the audience should repeat afterwards |
| Slides | One line per frame: its title as a claim |
| Backup | Expected questions, each with the backup frame that answers it |
| Vocabulary | The working terms the audience does not use (stage letters, document names, draft and report numbers, bookkeeping words) and the word the slides use instead |
| Sources | Where every figure and number comes from, which diagrams, tables and navigation strips of the written work the deck reuses, and any number computed for the talk alone |
| Formats | Audience PDF; the device the presenter presents from and a `.pptx` if it needs one; speaker notes only if the presenter uses them |
| Dense frames | Main frames excepted from the word cap or the in-figure font floor, each with its reason |

Budget about one main frame per minute of the slot. Once the budget is full,
a new main frame names the frame it displaces. The rehearsal measures the
time; the storyline carries no time mark per frame.

### The skeleton

The presenter judges a deck by looking at it, so the first thing they confirm
is a rendered skeleton, built in the first session: every main frame with its
claim as the title and a placeholder naming its figure, in order, without
polish. Check the skeleton against the brief before showing it: each thing the
brief asks for has a frame, and nothing the brief excludes has one. The
presenter confirms or reorders the skeleton; polish starts after that. Record
any choice made without them (an order, a dropped topic, a figure selection)
as an agent default in the storyline.

After the confirmation a structural change (a frame added, merged, dropped or
moved to backup) goes back to the presenter as a question of its own, with
what the audience loses, never inside a list of other calls. Wording, naming
and layout are agent defaults: decide, apply and report them.

## Slide rules

- **The title states the claim.** "Thresholds shift the cell energy peak", not
  "Cell energies". A frame whose claim cannot be named is two frames or none.
- **One idea per frame, in few words.** The slide holds the words and figures
  the speaker points at, in short sentences. The gate fails a main frame that
  sets more than 120 words on the slide (title, labels, tables and source
  lines count; text inside an included figure does not). Cut the text or move
  detail to a backup frame; a frame that must stay dense is listed under Dense
  frames with its reason.
- **The audience's words.** Use the terms the audience uses. The storyline's
  Vocabulary list becomes the gate's `--forbid-text` file with the first
  draft, so a working term cannot return to a slide.
- **The presenter's style.** The presenter's last deck is the reference for
  the look: its questions frame, its sentence length, its way of drawing a
  recurring element. A reviewer reports on look and structure; the presenter
  decides them.
- **Reveal for the argument's order only.** Use `\pause` when the audience
  must see the problem before the answer, not to animate a list.
- **Mark the point to remember** in `CtpRed`, at most once per frame. In
  diagrams, keep the colour legend of the reports (blue work, mauve check,
  green result, peach a person's step).
- **Cite public sources on the slide.** A figure or number from a published
  source carries a `\scriptsize` source line; a figure adapted from a paper
  says "Simplified from" or "Adapted from". The references frame lists them
  all. For an audience outside the presenter's group, no slide names the
  group's unpublished documents (reports, notes, draft numbers) or their
  review status; that provenance stays in the storyline's Sources. A talk
  inside the group follows the group-meeting rules below.
- **Boxes and commented equations.** Put a definition, a key number or the
  take-away in a filled block; comment an equation's terms in place with
  `\underbrace` or `\overbrace` instead of a "where ..." list below it.
- **Structure.** Title, the question alone on one frame, sections (metropolis
  shows progress), the take-away frame, references, a questions frame, the
  appendix, then a blank frame to draw on. Frames show their number alone,
  not n/N; `appendixnumberbeamer` keeps backup frames out of the count.
- **Backup frames** answer expected questions. Link each from the frame that
  raises it (`\beamergotobutton`) and back (`\beamerreturnbutton`).

### Figures

Use the figure files of the plotbook or report as they are, so the slide shows
the reviewed figure with its provenance. Never crop away an axis, its title or
a legend to make a figure fit. On a main frame the audience must read the
figure: when the gate fails text inside it for size, re-render the plot at
slide size through the plot's own recipe
([scientific-plotting](../../scientific-plotting/SKILL.md)), or list the frame
under Dense frames when the figure cannot be re-rendered (a published figure)
or is shown as an impression (a full table). On a backup frame small text in
a figure is a flag. A plot made for the talk goes through the study's plot
recipe too; do not redraw data by hand in the slide. Text set on the slide
itself keeps the fail floor everywhere. A TikZ diagram counts as a figure:
the template's hooks mark it, so its labels are left out of the word cap and
follow the figure rules above; an overlay annotation (`remember
picture,overlay`) stays slide text. One figure per
frame when the figure is the argument.

### Numbers

Every number on a slide comes from the artifact that owns it: the study's
generated number macros, or a generator script that reads the owning table and
asserts that its totals equal the owner's. Before a count enters a title, find
the artifact that already states it and use that definition. A headline number
names the configuration it belongs to. A number computed for the talk alone is
listed as such under Sources and checked by the claims review.

### Diagrams and navigation

When a talk from your own study uses a diagram or navigation strip of the
written work, it shows the same one, so the numbers on the slide are the
reviewed ones.

- **Input the asset, do not redraw it.** A study keeps each diagram in its own
  file, `assets/<name>.tex`, fed by the generated number macros
  ([report-writing](../../report-writing/references/report-production.md#diagrams-as-asset-files)).
  The deck inputs that file and the macros, so the slide shows the reviewed
  numbers and follows the next revision. A diagram still inline in the report
  moves to an asset file first, unchanged; the report's rendered pages must be
  identical before and after the move.
- **Scale as a whole.** `\resizebox` the diagram to the text width, then check
  its labels against the gate: a `font-below-advisory` finding is a flag; a
  `font-below-floor` finding needs a slide-sized variant of the picture in the
  same asset file, fed by the same macros.
- **Show the position.** When the written work has a navigation strip (a strip
  of the processing chain with the current step highlighted), input it
  unchanged as metropolis's `frame footer` template, left of the frame number,
  on each frame about one step, and leave it off frames about the whole study.
  The footer is light, so the strip keeps its colours; the dark title bar would
  need a recoloured copy.
- **Colour keys travel with the diagram.** Define the asset's colour names in
  the deck as aliases of the deck palette, never as new values.

## Kinds of talk

### A talk from your own work

A defence, colloquium or seminar from a thesis, study or report.

1. Take the question, findings and limits from the accepted report or
   `RESULT.md`; the talk adds no claim the written work does not support.
2. Choose depth by audience: a committee checks method and validity, a
   seminar audience wants the idea and the result.
3. Move derivations, detector and software details to backup frames rather
   than deleting them.

**Re-cut** for another audience or slot: write a new storyline from the
existing deck, keep the frames that serve it, move the rest to backup, and
record what was added, moved and removed. A thesis colloquium becomes a
seminar this way: new frames where the second audience needs an intermediate
step, a shorter background appendix.

**Someone else's paper** (journal club, course seminar): read the paper in
full and separate its claims from your assessment
([teach](../../teach/SKILL.md) helps here). Add a section on strengths,
limits and your own view or questions, and cite the paper on every frame that
uses its figures. When the talk is graded, map every rubric item to the frames
that answer it in the storyline and check the map before delivery.

### Group-meeting update

Three to eight frames from a study in progress.

1. First frame: what changed since the last meeting and the question for the
   group.
2. Then the plots that show it, from the current plotbook, each with its
   reading in the title.
3. Last frame: open questions, decisions needed from the group, next steps.

Numbers and claims come from the study's report or `RESULT.md`, with their
review status (a result awaiting review says so on the slide). An update
presents the study; it draws no new conclusion.

### Poster

A reader stands one or two metres away for a few minutes. The template is A0
portrait in blocks: question, method, result, take-away, references. The title
states the result; the result block's figure is the largest element. Besides
the gate, whose `gate` subcommand uses the default font floors, run the poster
floors as a second check:
`python3 <render-review>/scripts/render_gate.py lint-pdf poster.pdf --profile slides --min-font-pt 18 --flag-font-pt 24`.
These values are for A0; multiply both by 0.71 for A1.

## The presenter's source

The presenter edits the deck too, so the source is theirs from the first
draft:

- Deliver the source folder with the first draft, with one command that
  builds it and one that rebuilds on every save (template `Makefile`).
- One agent writes to it at a time; a second session reads, or waits.
- Before each build, diff the source against the last agent build. The
  presenter's edits stay word for word; a change their text needs is a
  question to them.
- Each request the presenter makes becomes an assert in `check_requests.py`
  (template), run on every build, so a request once met stays met.

## The rehearsal pack

The presenter must be able to defend every frame, and finds out whether they
can by giving the talk aloud. Speaker notes and a walk-through do not replace
that. Deliver one document with the first full draft and refresh it with the
final:

- **Setting**: audience, slot, who speaks before; the deck file it describes,
  as the only source for the talk's order and wording.
- **Per main frame, by PDF page**: the points to hit, number first; the terms
  on it the presenter must be able to define.
- **Expected questions**: each with an honest short answer and its backup
  frame. "Not yet measured" is an answer; it should sound like a plan.
- **What changed** since the last rehearsal.
- **How to run it**: the coach stays quiet and times each frame; afterwards,
  in this order: total time against the slot and the frames that ran long;
  what was said that the slide does not show; main claims left unsaid; flow;
  delivery; the three changes that would help most; then a question drill.

The pack is the brief for a rehearsal coach: an assistant in a voice session,
or a colleague. Aim for a timed run the day before the talk and another on the
day when the schedule allows. Its findings come back to the deck: an overrun
is fixed by cutting or merging frames, not by speaking faster, and a number
the presenter keeps misstating means the slide's wording changes. Record the
run times in `STATE.md`.

Write `\note{}` text and build the presenter copy (template README) only
when the storyline's Formats say the presenter uses notes.

## Build and review

1. Build the audience PDF (template `Makefile`), inspect the log and run
   `check_requests.py`.
2. Run the render gate on the audience PDF with `--profile slides`,
   `--backup-from` (the PDF page of the first backup frame), `--dense-frames`
   and the vocabulary's `--forbid-text` file
   ([render-review](../../render-review/SKILL.md)): overlays are grouped into
   frames by page label, whitespace is not a finding, and text crossing the
   slide edge, text below the floor and a main frame above the word cap fail.
   Fix blocking findings in the source. The gate is a mechanical check; it
   does not review the deck.
3. Claims review by an independent reviewer at each change of source (a new
   revision of the study, a number computed for the talk) and before the
   draft that goes to the person named in the brief: every number, scope and
   claim against its source. Check a wording the reviewer proposes against
   the source before applying it.
4. Independent visual review at three milestones: the skeleton (order and
   claims against the brief), the draft that goes to the person named in the
   brief, and the final. Use a capable image model, not the economy route,
   and give it rasters of each selected frame's last overlay at projection
   size, numbered by PDF page, with the presenter's last deck as the
   reference. A talk must look finished: the reviewer accepts or rejects each
   frame, and any of these is a reject, fixed in the source and reviewed
   again:
   - the claim is not readable from the title and figure;
   - a plot lacks an axis, its title or its legend;
   - an element clashes with the surface it sits on, such as a white or boxed
     element on the dark title bar;
   - frames with the same role (two figure frames, two backup frames) are
     styled differently (fonts, sizes, boxes, the navigation strip);
   - the layout is unbalanced or looks unfinished: content crowded in a
     corner, an empty half, edges that do not align;
   - text set on the slide is too small for the back of the room, or wraps
     badly, collides or clips.

   The brief names this standard and never tells the reviewer to ignore
   colour or layout. Select the title, question and take-away frames, every
   frame with a figure or diagram, and every frame changed since the last
   review; after a change to the palette, fonts, title bar or footer, review
   every frame. A draft between milestones gets steps 1 and 2 and the
   author's own look at each changed page; record it as checked by the
   author, without independent review.
5. Copy review on the storyline and the deck source for a talk others will
   judge; a short group-meeting update may skip it. A graded talk checks the
   storyline's rubric map here.
6. Export the PowerPoint copy when the storyline lists it:
   `python3 <presentations>/scripts/export_pptx.py deck.pdf --out deck.pptx`.
   It holds one picture per PDF page (and the notes with `--notes`); edit the
   source, not the `.pptx`.
7. Deliver the PDF (and `.pptx`) and the rehearsal pack to the user's review
   inbox, if the project has one
   ([consequential actions](../../session-coordination/references/consequential-actions.md)),
   as awaiting review. Uploading to a meeting page or sending to the audience
   is the presenter's step.

### The day of the talk

Late requests are normal: a supervisor's last look, a meeting that morning.
Apply them directly on the presenter's word, without a freeze. Each build
gets steps 1 and 2 and a look at every changed page, and no independent
review; a number or plot added that day names its source in the storyline.
After the presenter has uploaded the deck, write one closing record in the
session: the file presented (name, page count, hash), what changed that day
and on whose request, what went unchecked, and the rehearsal times.

### After the talk

Mine the session for what the presenter corrected more than once and what the
rehearsal found ([reflect](../../reflect/SKILL.md)), and route each lesson to
the file that owns the rule.
