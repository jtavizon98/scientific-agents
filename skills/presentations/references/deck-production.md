# Deck production

The procedure behind the [presentations](../SKILL.md) skill: the storyline
contract, slide rules, the kinds of talk, notes and questions, build and
review. The [template](template/README.md) implements the conventions named
here.

## The storyline contract

The audience hears a talk once, in order, at the speaker's pace, and cannot
turn back, so settle the argument before drawing any slide. Write the
storyline in the session record and get the presenter's confirmation:

| Field | Content |
| --- | --- |
| Kind | Own work, re-cut, someone else's paper, group-meeting update or poster |
| Audience | Who listens, what they already know, what they will do with the talk |
| Slot | Length of the talk and of the questions |
| Question | The one question the talk answers |
| Take-away | One sentence the audience should repeat afterwards |
| Slides | One line per frame: its title as a claim, and a time mark |
| Backup | Expected questions, each with the backup frame that answers it |
| Sources | Where every figure and number comes from, and which diagrams, tables and navigation strips of the written work the deck reuses |
| Formats | Audience PDF and presenter copy; a `.pptx` if the room needs PowerPoint |

Budget the time per frame and check the total against the slot; one to two
minutes per frame is a usual pace, slower for a dense result. Budget a frame
with `\pause` reveals once; its overlays share the frame's time. Record any choice made without the presenter (an order, a
dropped topic, a figure selection) as an agent default in the storyline, and
build on it; the presenter can reverse it at the confirmation.

Changes to the storyline after confirmation go back to the presenter before
the slides change.

## Slide rules

- **The title states the claim.** "Thresholds shift the cell energy peak", not
  "Cell energies". A frame whose claim cannot be named is two frames or none.
- **One idea per frame.** The slide holds the words and figures the speaker
  points at; the sentences belong in the notes.
- **Reveal for the argument's order only.** Use `\pause` when the audience
  must see the problem before the answer, not to animate a list.
- **Mark the point to remember** in `CtpRed`, at most once per frame. In
  diagrams, keep the colour legend of the reports (blue work, mauve check,
  green result, peach a person's step).
- **Cite on the slide.** A figure or number from a source carries a
  `\scriptsize` source line; a figure adapted from a paper says "Simplified
  from" or "Adapted from". The references frame lists them all.
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
the reviewed figure with its provenance. The slides gate flags small text
inside a placed figure rather than failing it; whether to re-render a plot at
slide size is the deck owner's choice, through the plot's own recipe
([scientific-plotting](../../scientific-plotting/SKILL.md)). Text set on the
slide itself, including TikZ labels, keeps the fail floor. One figure per frame
when the figure is the argument; say in the notes what to look at.

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

## Notes and questions

Every content frame gets a `\note{}`: what to say, what to point at, and the
time mark. Build the presenter copy with the notes on a second screen
(template README). The questions list in the storyline maps each expected
question to its backup frame.

The presenter must be able to defend every frame. Walk them through every
frame they did not draft (all of them when the agent built the deck) with a
[teach](../../teach/SKILL.md) pass: they explain the frame back, and the gaps
become notes or backup frames. If the presenter is away, record the
walk-through as pending in `STATE.md` and deliver the deck as awaiting review.

## Build and review

1. Build the audience PDF and the presenter copy from the same source
   (template README); inspect both logs.
2. Walk the presenter through the frames they did not draft (Notes and
   questions) and rebuild with the notes and backup frames that come out of it.
3. Run the render gate on the audience PDF with `--profile slides`
   ([render-review](../../render-review/SKILL.md)): overlays are grouped into
   frames by page label, whitespace is not a finding, and text crossing the
   slide edge or below the floor fails. Fix blocking findings in the source.
   The presenter copy needs only a clean build log.
4. Visual review through an economy image-capable route, on rasters of each
   selected frame's last overlay at projection size. A talk must look
   finished: the reviewer accepts or rejects each frame, and any of these is
   a reject, fixed in the source and reviewed again:
   - the claim is not readable from the title and figure;
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
   every frame.
5. Copy review on the storyline and the deck source with notes for a talk
   others will judge; a short group-meeting update may skip it. A graded talk
   checks the storyline's rubric map here.
6. Export the PowerPoint copy when the storyline lists it:
   `python3 <presentations>/scripts/export_pptx.py deck.pdf --notes deck-notes.pdf --out deck.pptx`.
   It holds one picture per PDF page and the notes; edit the source, not the
   `.pptx`.
7. Deliver the PDFs (and `.pptx`) to the user's review inbox, if the project
   has one ([consequential actions](../../session-coordination/references/consequential-actions.md)),
   as awaiting review. Uploading to a meeting page or sending to the audience
   is the presenter's step.
