# Report production

Produce working explanations as coherent LaTeX/PDF artifacts. A report is a
designed explanation, not an append-only record of the work that produced it.
Its structure, level of detail and evidence presentation are part of
correctness.

LaTeX owns the editable human-facing source while operational claims derive
from canonical Markdown and primary evidence. The rendered PDF is the primary
review, decision and delivery surface. Generated PDFs are usually excluded from
version control unless the project decides otherwise; their ignored status does
not reduce their importance during review or handoff.

## Audience and authority

Scientific figures embedded in a report follow the project's plotting workflow
(see [scientific-plotting](../../scientific-plotting/SKILL.md)). Reuse the
project's plotting library and the applicable accepted plotbook recipe, display
binning and style; report typography and layout are not permission to create an
independent scientific renderer.

For an audit, define the reader's verification task before choosing length or
inventory. Trace each material claim through its definition, delivered figure
and underlying numerical or source record, including what it cannot establish.
The report and companion plotbook together must provide a usable route; a list
of file paths outside the PDFs does not replace it.

- Markdown is the canonical agent-facing operational record for policy,
  procedures, current facts, constraints and session evidence.
- LaTeX is the editable source of the explanation. It may reorganize and
  visualize the Markdown workflow, but does not override it.
- PDF is generated from LaTeX and is the primary surface the reader uses to
  evaluate the work. It stays untracked unless the project decides to track it.

Agent-produced report prose is a working explanation, not thesis or publication
prose. The repository author's rule, which a user may drop or replace with
their institution's: the user writes any text intended for a thesis, paper or
external audience. Follow the user's academic and disclosure rules for what an
agent may draft. Checked tables, plots, diagrams, equations, evidence and document
structure may be reused, but that reuse does not convert the report's prose into
publishable copy.

For a substantial explanatory report, the active session also owns a durable
reader and methodology map (for example `METHODOLOGY_KNOWLEDGE_BASE.md`). It
records:

- the intended reader and purpose;
- subject matter, terminology, mathematics and tools the report may assume;
- the relevant coursework, literature and existing project documentation;
- unfamiliar or domain-specific methods that require motivation before use;
- standard sourced methods versus custom diagnostics or extensions;
- open factual or methodological checks that constrain the report's claims.

The report plan and the active session state must link this file. The report
itself should identify its reader assumptions briefly and cite the mapped
sources where methods are introduced. This preserves the explanatory contract
through context compression, interruption and handoff without copying the full
map into LaTeX.

When an operational rule changes, update its owning Markdown first, then update
any affected LaTeX guide and rebuild the PDF. If they disagree, Markdown wins
and the discrepancy must be corrected rather than rationalized in the PDF.

## Choose the artifact

Define the reader's question, decision or use, status and evidence sources
before selecting a document form.

| Form | Use when | Typical structure |
| --- | --- | --- |
| Memo | One bounded question can be answered in a few pages | Purpose, finding, evidence, decision or next action |
| Article | One study needs a continuous argument with limited supporting material | Summary, context, method, evidence, interpretation, conclusion |
| Book | Several dependent questions, substantial reference material, or a durable technical record need chapters and appendices | Front matter, current-state chapters, decisions, verification, reference appendices |

The minimal template in [template/](template/README.md) is for memo and short
article work. Do not force a substantial artifact into it. Prefer the lightest
form that gives the reader a clear route through the material, not the form that
requires the fewest source edits.

## Inspect before editing

For an existing artifact, establish the whole argument and inspect its source,
contents, evidence map and prior review record. Reuse that orientation during
local revisions; inspect affected source and rendered pages rather than
repeatedly reading every unchanged page. Then choose one of three edit modes
and state the choice before writing:

- **Patch:** the organizing model still works and the change is genuinely local.
- **Structural revision:** the argument is sound but sections, evidence or
  front/back matter need consolidation or reordering.
- **Rewrite:** the current organizing model no longer answers the reader's
  question cleanly.

A rewrite or substantial structural revision is warranted when one or more of
the following persist:

- the same claim or context appears in several sections;
- chronology dominates the main explanation;
- new findings are appended without reconciling earlier conclusions;
- tables expose raw source expansion instead of the entity or comparison the
  reader needs;
- terminology is introduced after it is required;
- the document class or template no longer matches the scope;
- additions make the artifact longer without making its conclusions easier to
  find or verify.

For a substantial explanatory artifact, inspect or create the session's
methodology knowledge base before outlining. Do not infer the reader's
knowledge only from the existing draft: a terse or jargon-heavy draft may be
evidence that its reader model was never made explicit.

Do not interpret "smallest coherent change" as "retain the most existing text."
Deletion, consolidation, reordering and rewriting are smaller than continued
patch accumulation when they restore one clear organizing model.

Dated revisions of a report keep every earlier presentation, so a new revision
carries over what serves the current question, not every inventory, diagnostic
or layout that served an earlier one. Once a question is settled, its
presentation may be retired or replaced. Name what was dropped in the session
record.

## Design the argument

Outline the reader's path before drafting prose. For a substantial technical
report, assign each type of content one role:

1. Front matter states purpose, status, scope and terminology needed to read
   the report.
2. The main body explains the present state in the order the reader needs it.
3. Evidence appears next to the claim it supports, at the reader's useful unit
   of comparison.
4. Decisions, limitations and unresolved questions are explicit.
5. Independent verification follows the claims it checks rather than
   interrupting their explanation.
6. Exhaustive catalogues, provenance, chronology and superseded
   interpretations move to appendices or a journal.

Use the durable knowledge base to decide where definitions and derivations are
needed. Prefer methods already developed in the reader's coursework or mapped
references when they answer the question correctly. If a necessary method is
absent, explain why it is needed, connect it to familiar concepts, and cite an
authoritative source or provide the required derivation and limitation. Do not
present a custom diagnostic as a standard method.

The exact headings depend on the question. Do not turn this sequence into a
fixed table of contents.

Keep source data separate from presentation when tables are numerous or
repeated. Generate derived tables from validated data rather than maintaining
the same facts manually in prose and LaTeX. A table should answer a named reader
question; one row per raw record is not automatically the right presentation.

### Choose form by information structure

Construct the target concept directly. Do not organize a definition or reference
table around a misconception that the reader must first hold and then reject.
State a concrete operational prohibition only when violating it would change the
physics, computation or interpretation, and give that rule one authoritative
home.

For personal working reports, one recommended ordering of forms for explaining
something (a preference of the original author, adapt it to your reader):

1. (a) plots, sketches and diagrams; (b) commented equations, each term
   explained beside the equation;
2. lists and tables;
3. prose.

Build the aids first: decide which figures, diagrams, equations and tables a
section needs and make them. Then write the prose that presents the argument and
complements the aids. A code or pseudo-code snippet is allowed when it explains
what the code does more clearly than prose would, though a diagram or list
usually does it better. A changed aid is also easier to spot between dated
revisions than a changed sentence in a paragraph.

To show how settings change along a chain of stages, draw a change map, not a
table of every setting's state at every stage. Rows are settings, columns are
the transitions between neighbouring stages, and a marker sits only where a
setting changes; an empty cell means kept. Settings that never change go on one
"kept at every stage" line. Use at most four reasons for a change, each with its
own marker, and define them in the prose and in a key above the table. A table
of states with bracketed codes makes the reader decode each cell before seeing
what changed.

A shorter report keeps every setting that affects the results; it states the
rule a setting implements, such as which objects enter a weight. Implementation
provenance (file paths, operand encodings, identity checks, inventories) moves to
the session's `RESULT.md` or a code-reading guide, with a note of what moved and
where. The bibliography stays in the report.

The target is a short time to read and digest, not a short page count. Note
style is fine while it stays clear; bloat is not. Prose is harder to parse
quickly than tables, plots, diagrams and lists. The test for a paragraph: would
the reader need to re-read it to follow it? Then turn it into an aid or split it
around one.

Within that order, identify the content's information structure in the outline
(ordered process, parallel chains, population comparison, mathematical
definition, interpretation) and pick the form that makes it directly readable:

- plots for trends, distributions, correlations, residuals and numerical
  comparisons whose pattern matters;
- diagrams or sketches for chains, spatial relations, branching decisions,
  dependencies, set relations and interfaces that cannot be read as a simple
  sequence;
- commented equations or aligned derivations for mathematical constructions;
  number every equation that a figure, table or later section uses;
- numbered lists for linear procedures;
- aligned columns or a comparison table for parallel processing chains, with
  each chain's order explicit; align shared phases without implying equivalent
  cuts;
- tables for compact exact values, categories and repeated fields;
- prose for motivation, causal reasoning and the links between aids.

A diagram is not evidence merely because it is visual. Data-free schematics
explain relationships; plots and validated numerical tables present empirical or
computational evidence. When only a source plot exists, reproduce or excerpt it
with exact provenance rather than digitizing values without a validated data
source. Keep compact evidence compact, but prefer a plot when the reader needs to
recognize a shape or pattern before inspecting exact values.

In the coherence pass, check that readers need not reconstruct a sequence,
parallel comparison or population partition from prose. Make overlapping
totals and exclusive categories explicit. Reorganize when the story jumps: a
definition or equation sits next to its first use, not pages away from the
section where it pays off. The copy review (see
[Tiered review](#tiered-review)) tests these choices against the actual reading
task.

Raw plotbooks, logs and generated tables are supporting evidence, not an
adequate review surface by default. Curate and label the material needed to
answer the reader's question in the report or an organized appendix. Deliver a
raw artifact separately only when the reader explicitly requests it.

### Diagrams as asset files

Keep each diagram that more than one artifact shows (report, plotbook, talk)
in its own file, `assets/<name>.tex`, holding only the picture, with a comment
naming the packages, colours and macros it needs. Any number in it comes from a
macro written by the analysis from its validated results, never typed in. Each
artifact then `\input`s the same file, so a revision reaches all three at their
next build. A navigation strip (a strip of the processing chain with the
current step highlighted) is a macro in the same folder. Moving an existing
diagram into an asset is a no-change edit: rebuild and compare the rendered
pages with those of the build before the move; they must be identical.

### Headlines, choices and colour

Use the template's boxes ([template/report.tex](template/report.tex)):

- **Headline.** A section whose result fits in one or two sentences opens with
  them in a `headline` box; the material that follows gives the details. Do not
  hold the payoff until the end of the section.
- **Choice.** Every choice for the reader is a `choice` box, itemized, with a
  recommendation, an alternative where one exists, and links (`\ref`) to the
  plots, tables or sections that support each option. A choice is never left
  inside a paragraph.
- **Colour as a reading aid.** Shade table rows so they are easy to follow, mark
  outliers in tables, colour list markers or diagram paths that the reader must
  find again, but avoid a rainbow. Tint a row, symbol, brace, label or path
  rather than whole passages. Each colour keeps one meaning within its scope and
  has a textual or symbolic cue; the palette below applies, and the artifact must
  stay readable in grayscale.
- **Look at the source.** Where opening an output file, calibration file or
  code would show the reader something the report's summary, tables and plots
  cannot, say so and direct them to it with the exact path (and object, branch,
  key or `file:line`) and what to look for there. For example, the per-event
  weight branches behind a weight summary.

## Write the companion after settling the plotbook

When the task requests a plotbook and companion, establish evidence coverage and
a provisional argument early. Finalize prose, figure references and navigation
after the plotbook's comparisons and layout have passed its reading tests. Record
both final report and plotbook identities (hashes) and the plotbook page map.
If drafting reveals a missing comparison or an unclear figure, reopen the
figure/plotbook loop rather than writing around the gap. A pagination or
scientific change reopens affected report routes and claims.

As a recommendation, read the plotbook before the report's interpretation, so
that the report's reading of the plots does not anchor yours (the Einstellung
effect).

The companion explains how the evidence answers the reader's question. Assume
the agreed domain knowledge, not knowledge of the agent sessions. Introduce the
problem and main finding, then the evidence identities and investigations in the
order needed to understand them. For each finding, make the question,
observation, interpretation, limitation and figure route available without
forcing identical paragraph templates. Explain a population before its ratio and
a method before its result. A short worked example can resolve a difficult
distinction more clearly than repeated qualifications.

Keep explanatory transitions brief when the contract asks for a concise
companion. Give recurring conventions one home; use a compact lookup for
exhaustive coverage and provenance. Do not reproduce the distribution catalogue
or its captions as report prose. Length follows the reader task; no page count
and no tutorial expansion is a default.

## Source traceability and corroboration

A broad statement that a report is "derived from" a directory is not enough to
corroborate its claims. Cite important factual, operational, numerical and
decision claims where the reader encounters them. Use the nearest source that
owns the claim:

- an evidence claim (what a run produced, what code or a configuration does)
  cites a machine-generated source, such as a runtime output, log, executed
  configuration, or code `file:line` at a commit, or a human-generated source,
  such as official documentation, a wiki topic, a paper or a maintained manual;
- a session record (brief, state, result, handoff, decision, review and worker
  records) is cited only for the owner's decisions and for review acceptance,
  never as evidence of a measured or implemented fact: prefer hard machine
  sources (logs, outputs, code) or human-generated sources over agent sessions
  and records;
- a small cited artifact (configuration, log excerpt, JSON summary) is copied
  with its sha256 into the session's `evidence/` folder and cited there with its
  original path, because scratch storage is not durable; classify it under the
  project's content-classification rules before staging. A large artifact stays
  in place with its path and sha256 recorded in `evidence/`;
- a policy or procedure claim cites the canonical Markdown file and subsection;
- volatile topology, branch, host, service and current-state claims carry a
  verification date or revision;
- a derived conclusion cites every source needed to reproduce it rather than
  only the document that later summarized it.

A session record may document a decision, but it is not evidence that the
decided thing happened, and it does not override the canonical workflow that
governs what should happen.

### Source hierarchy

Cite the source that owns a claim, not an internal note that summarizes it, with
at most one deliberate exception: a maintained project register that owns a
class of claims and their external citations (see the next item). Survey notes,
session Markdown and review records cite only this project's own measurements,
decisions and reviews; an external fact they summarize is cited at its origin.

- Recommendation and deprecation claims (which setting is current, what replaced
  what and why) cite the entry in the project's maintained manual or register
  when one exists, with the entry's section as pinpoint. The register owns their
  external citations and records where documentation and code disagree. If an
  entry is missing, add it to the register rather than citing the external
  source from the report.
- For reasoning and tool usage, prefer human-facing documentation: official
  group pages, wiki topics with their revision, tool documentation, papers and
  technical notes. They state the reasoning; source versioning is precise but
  harder to digest.
- Cite Git as well (merge request, commit, or `file:line` at a named tag) when the
  human-facing documentation does not point to the change, or when explaining
  exactly how a tool behaves. A behaviour table with file and line pinpoints is
  appropriate there; a hash alone is not an explanation.
- When a needed human-facing source is login-restricted or unread, ask the user
  for a browser session rather than substituting an internal note, and mark the
  claim open until the source is read. Harness recollection, chat transcripts
  and agent memory are leads to verify, not sources to cite as operational
  truth.

For a substantial report, use claim-level citations plus a source register or
bibliography. A useful entry records the repository-relative path or stable
identifier, the source's role, the relevant revision or evidence date, and any
access restriction. Pinpoint the subsection, table, figure, record or line of
evidence in a footnote when the source is longer than the claim being checked.
Tables and figure captions need the same provenance when they encode sourced
facts.

Use the source's own printed or document page numbers for citation pinpoints,
not raw PDF-viewer indices. Give every source in a grouped citation its own
pinpoint, and name the cited edition when its pagination differs from another
listed edition. When a source has no meaningful pagination, cite the exact
section, figure, record or versioned documentation anchor instead. Never guess
a pinpoint; leave the gap explicit until the source can be checked.

When sources disagree, do not choose one silently. Identify the discrepancy,
name which source is authoritative for that claim, and either correct the stale
source or mark the report claim unresolved. Record the corroboration pass in the
owning session state.

A bounded source review corroborates changed claims and their immediate
dependencies against the cited sources. For a substantial report, one complete
source review covers the report's important claims, citations and source
register after bounded source reviews pass. Repeat it only when later edits
change the source hierarchy, evidence base, or claims outside the bounded
correction scope.

### Bibliography and reader-verifiable pinpoints

For new substantial LaTeX reports and substantial rewrites, use a shared
bibliography library and linked citations, as described in
[source-library](../../source-library/SKILL.md). This lets the reader check the
report without asking the author where a claim came from. Use `biblatex` with
`backend=biber`, BibTeX-format shared `.bib` databases, linked citations and
`backref=true`. Biber is the processor; do not mix this setup with the legacy
BibTeX backend or a hand-written `thebibliography`. Links are blue, not hidden
(a recommendation, and the template's default): hyperref `colorlinks=true` with
`citecolor`, `linkcolor` and `urlcolor` set to the template's `ctpBlue`, never
`hidelinks`. A local patch to an otherwise sound older report does not require
an unrelated bibliography migration.

Each source has one owning entry and a consistent descriptive shorthand across
reports. Load literature, workspace and topic-based study resources as needed;
never create another report-local copy. Register independently citable records
or defined evidence collections, with member-file pinpoints and manifest routes.
Preserve specifically cited historical versions and distinguish inspection dates
from source dates. Frozen historical artifacts retain their identity when the
library is migrated.

Use `style=alphabetic`, `sorting=nyt`, `giveninits=true` and `maxbibnames=8` as
the working default. Short, unambiguous `shorthand` labels may make frequently
cited sources easier to recognize. Preserve complete checked metadata: author or
responsible organization, title, edition/version and date, DOI or stable URL
where available, and access restrictions. For repository sources, give the exact
relative path, owning role, and inspected revision or date. Do not invent public
URLs for private files or claim that a dirty working copy was published at its
base commit.

Put the pinpoint in the citation postnote, next to the supported claim:

```latex
\cite[p.~23, sec.~3.9]{source-key}
\cites[pp.~10--11]{first-key}[sec.~2]{second-key}
```

These are syntax examples; replace the keys and pinpoints with inspected
sources. Each source in a grouped citation needs its own locator. A source's
`pages` bibliography field describes its publication extent or article number;
it does not locate the passage supporting a particular claim. Cite the source's
printed pagination and checked edition, adding section, equation, table or
figure identifiers where useful. Unpaginated Markdown requires a named section
or record instead of an invented page. A PDF inclusion's `page=` parameter is
an extraction index and may differ from the page cited in its caption.

Use the same citation standard for sourced tables, reproduced or cropped panels,
and derived figures. State which source supplies inputs and which supplies a
method when they differ. Bibliography back-references locate this report's uses
of a source; they are not source-page pinpoints. Check both directions in the
rendered PDF: claim to source entry, and source entry back to citing pages.

Build with `pdflatex REPORT.tex`, `biber REPORT`, and two further pdfLaTeX
passes (or an equivalent verified latexmk recipe). Inspect the Biber and LaTeX
logs for missing keys, duplicate keys, malformed data, unresolved references,
and rerun requests. Preserve the `.bib` as authored source; treat `.bbl`, `.bcf`,
`.blg`, `.run.xml` and the PDF as generated artifacts. If an external submission
requires a `.bbl`, handle that as an explicit delivery requirement.

Borrow a reference report's portrait layout, approachable reading routes,
restrained labelled colour, readable code blocks and dependency diagrams when
those serve the report's question. Adapt the presentation without importing
unrelated claims. Any source content actually reused retains its access
restrictions; adopting a layout alone does not determine content classification.
Record the reference and scope of adaptation in the reader/methodology map.

### Readable source and numerical presentation

Use latexindent with a project settings file for authored LaTeX: two-space
indentation and approximately 90-character prose lines. Preserve paragraphs,
deliberate equation/table breaks, code and verbatim content. Run the formatting
check before handback; formatting must be idempotent. Format generated tables
through their generator where needed, not by editing outputs.

Use siunitx for reported numerical values, quantities, percentages and units:
`\num{3084925}`, `\SI{25}{\giga\electronvolt}`, `\SI{0.0193}{\percent}`,
`\unit{\pico\barn}`, `\numrange` and `\SIrange`. Prefer `\SI` over `\qty` when
you also use the `physics` package, whose `\qty` sizes delimiters. Use `S` table
columns where decimal alignment aids comparison. Retain precision and explicit
uncertainty conventions; automatic rounding is not part of presentation cleanup.
Identifiers (dataset or run identifiers, hashes, versions), dates, code
literals, reference numbers and algebraic constants are not measured quantities.

Check prose, captions and tables for manually formatted values and units.
Detection can flag likely omissions; source review must distinguish identifiers
from quantities. New reports and revisions must pass this check, formatting and
LaTeX/Biber builds, followed by rendered inspection. The template demonstrates
the required setup. Existing historical snapshots retain their original source.

The checker is [scripts/check_report_sources.py](../scripts/check_report_sources.py).
It takes explicit `.tex` sources and reports duplicate bibliography keys and
shorthands across the shared library, `\addbibresource` targets outside the
library, hand-written bibliographies, formatting drift (`--write` applies it),
and, with `--quantities`, likely raw quantities. It needs `latexindent`. Paths
are arguments: `--root` (default: the current directory) bounds the sources,
`--bib-dir` names the shared library (default: `<root>/bib` if present;
without one, resources only need to exist), and `--latexindent-config` names the
settings file (default: `<root>/latexindent.yaml` if present, else latexindent
defaults). It exits non-zero on any finding. Its scan lists candidates, not
violations; review each.

## Writing character

Use direct, approachable scientific prose. Build explanations from motivation
to mechanism, procedure, evidence, interpretation and caveat. Define terms
before use; introduce a figure or table before interpreting it; state what is
observed before proposing why it occurs. Inclusive "we" and concrete visual
analogies are welcome when they genuinely make the reasoning easier to follow.

Do not import labels from other studies or sessions (for example J1, L1, S2a).
Use descriptive names such as "the 2023 detector-alignment correction" instead
of a code like "S2a". If a report must rely on such labels, restate them in the
summary and give a label table in an appendix.

Lists and tables may carry the steps of an argument; prose links them and states
the reasoning they cannot hold. Preserve technical language and calibrated
uncertainty. Avoid corporate phrasing, ornamental formality, generic transitions,
and prose polished into a voice unlike the author's. See the
[unslop](../../unslop/SKILL.md) skill.

## Colour convention

The template uses the Catppuccin Latte palette. Blue marks the canonical choice,
mauve a fallback, green a verified result, peach an open item, red a blocker,
and a yellow tint a proposal or catalogue-only treatment. In a choice box the
recommendation takes the canonical blue and the alternative mauve; the box
itself is peach because the choice is open. Every use must also carry an
explicit label or symbol. Color is a secondary cue, not the only way to
distinguish states. Check dense tables in color and grayscale during visual
review.

## Production workflow

1. Define the reader's question, use, status and authoritative evidence.
2. For a substantial explanatory report, create or update the session's durable
   reader and methodology map and link it from the report plan and session
   state.
3. Inspect the full artifact and choose patch, structural revision, or rewrite.
4. Select memo, article, or book and draft an outline with content roles, each
   section's headline and the aids it needs; make the aids before the prose.
5. Preserve provenance, add claim-level source citations, and separate
   observation, inference, decision, and proposal.
6. For a plotbook companion, settle its comparisons/page map before final prose
   and navigation. Draft the complete argument, then perform a coherence pass
   that removes repetition and stale conclusions.
7. Apply the tiered review policy below to source corroboration, copy,
   domain/numerical claims, and rendered pages.
8. Compile and inspect warnings before final rendered-page review.
9. Obtain human domain review where required.
10. Resolve review findings at their owning layer and rerun only the affected
    bounded gates unless an escalation trigger requires a complete pass.
11. Record what changed, remaining gaps, where the review artifact lives, and
    whether it is awaiting the domain owner's review.

## Review and release

Internal checks prepare a report for the domain owner; they do not replace the
owner's review of the PDF. Track the rendered review artifact, its delivery,
blocker escalation, completion notification, and source publication as separate
gates. Email or upload is a consequential delivery action and must name its
destination and artifact. A lifecycle or status signal from an agent tool does
not deliver a PDF.

After internal checks and requested delivery, a substantial report remains
`awaiting human review` until the domain owner accepts, supersedes, or closes it.
A revision returns it to `in progress`. A newer version delivered on the same
date replaces the pending one, which is marked `replaced before review`; a
version on a later date is delivered alongside it, and both stay
`awaiting human review`. `superseded` means the owner reviewed the earlier
version or decided its replacement.

## Tiered review

For independent comprehension and rendered-page checks, give the reviewer the
reader brief and artifact before the author's assessment. Ask it to reconstruct
the question, findings, supporting comparisons and limits without the session
narrative. It may reject the organizing model even when individual sentences are
correct. An earlier local copy pass does not establish whole-argument clarity.
The owner verifies each material claim-to-figure route in the final delivered
PDFs; copy review alone does not validate navigation, sources or numerical
conclusions. `copy-reviewer` is a role, not an installed tool; see
[SKILL.md](../SKILL.md).

The writing owner first inspects the diff and runs deterministic checks. During
iteration, review changed claims, sections, equations, evidence, or rendered
pages with enough context to judge them. Escalate a review track to complete
coverage when a bounded review finds a document-wide conflict or the report's
risk requires a final complete gate. Re-review corrections only at their
affected scope unless they change structure, argument order, source hierarchy,
global terminology, document-wide conventions, or claims outside that scope.

Ask every reviewer to separate findings from risks. A finding is shown by a
run or calculation, or names an exact missing assumption, contradiction or
unsupported claim at a cited line; it must be resolved. A risk without such
evidence goes in a separate list for the owner to weigh.

Apply that progression independently to source corroboration, copy,
physics/numerical/domain review, and rendered appearance. A substantial report
requires one complete-source copy review. If its conclusions depend on physics
or numerical claims, it also requires one complete-artifact review by a
[council](../../council/SKILL.md) after bounded findings are resolved, followed by human
domain review where required. Copy review does not replace source or domain
validation.

Complete coverage is cumulative evidence, not a demand to repeat every check in
each reviewer session. Bind accepted source/claim/numerical evidence to its
inputs; later reviewers assess the changed claims and dependencies plus
whole-argument coherence. Do not reopen source or physics acceptance for
typography, repagination or optional copy polish. Give each review track a
distinct question, existing evidence and stopping condition. Recompute
independently where the scientific claim warrants it, not merely because a new
reviewer has been dispatched.

Run the render gate in [render-review](../../render-review/SKILL.md) before
visual dispatch. Supply applicable value/inventory/plan inputs or hash-bound
equivalent evidence; absent checks are not assessed. `blocked: false` alone is
not readiness. Validate the explicit review request with `review-preflight`
(see [its procedure](../../render-review/references/workflow.md)).
Mechanical checks cover the complete artifact; visual review tests residual
readability and decoding on new/changed layouts, representative family members
and relevant flags. Final status does not mandate another all-page pass.
Never delegate a PDF to the visual reviewer: provide only selected reading-size
rasters, useful overview sheets, reference pages and necessary crops. Use an
inexpensive image-capable reviewer; record a specific reason for any expensive
escalation. Add selected grayscale diagnostics where color carries meaning. The
owner verifies coverage and distinguishes inspected pages from sampled families.

## Acceptance checklist

- The opening states the question, scope, conclusion, and status; current truth
  is distinct from history.
- Important claims have one primary home, claim-level evidence, and dated
  support where facts are volatile; source conflicts are explicit.
- Terms precede use, reader assumptions are current, and observations,
  interpretations, decisions, and proposals remain distinct.
- Tables and figures answer the prose's comparisons; exhaustive material does
  not obscure the argument.
- Aids carry the explanation and prose links them; sections open with a
  headline box; every choice for the reader is a choice box with a
  recommendation, an alternative and evidence links; definitions sit beside
  their first use.
- Evidence claims cite machine or human sources, session records appear only
  for decisions and review acceptance, and recommendation claims cite the
  project's maintained register where one exists.
- Bibliography metadata and claim-level pinpoints are checked; Biber resolves
  all cited keys, and blue citation links and bibliography back-references work.
- Required source, copy, domain, build, and visual gates pass with residual gaps
  recorded. The render gate on the final PDF is unblocked, with any waivers
  recorded in the session state.
- Mechanical evidence covers the complete artifact. The bounded visual request
  passes preflight, covers residual tasks and records selected pages, family
  sampling and carried evidence. Neither final status nor page-count change
  alone triggers exhaustive inspection. Review evidence never claims that a
  vision worker read a PDF or inspected unsampled pages.
- Reading tasks succeed on the composed artifact; not-assessed or unresolved
  material findings are explicit. A companion identifies the exact plotbook and
  its routes match the final page map. A successful build is not a clarity
  verdict.
- The exact PDF, human-review state, delivery, notification, and source
  publication state are recorded separately.

## When HTML earns its cost

Use a self-contained HTML artifact when the task needs interactive comparison,
annotation, relationship diagrams, or a custom editing/review interface. Do
not choose HTML merely because of the device the reader uses. Preserve all
source commitments and keep a non-interactive summary where decisions need
durable review.
