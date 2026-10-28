# Scientific agents

Workflows for using agents in scientific research: inspect sources, settle
decisions, write and validate code, produce figures and reports, and hand work
between sessions without losing its evidence.

These are practices extracted from a working thesis setup. Take what helps,
change it for your project, and leave the rest. You do not need to reorganize
your thesis or use every skill. This first extraction is under review; see
[migration status](MIGRATION.md) for what is implemented and what remains.

## Start with a task

| You want to… | Start here | Take along |
| --- | --- | --- |
| Settle a substantial decision before implementation | `skills/grilling/` | The skill directory |
| Write scientific code with inspectable reasoning | `skills/scientific-coding/` | Its reference files |
| Structure and review a substantial report | [Report writing](skills/report-writing/SKILL.md) | Your project's writing workflow and reviewer tools; full report workflow extraction pending |
| Read sources, including through a logged-in GUI session | [Source discovery](skills/source-discovery/SKILL.md) | [Evidence handoff](templates/source-handoff.md) |
| Maintain one citation library across reports | [Source library](skills/source-library/SKILL.md) | [Bibliography workflow](workflows/source-library.md), [citation example](examples/citations/README.md) |
| Adapt existing plotting to review checks | [Plotting integration](skills/plotting-integration/SKILL.md) | [Plot evidence](workflows/plot-evidence.md), [render checker](workflows/render-review.md), [two-renderer example](examples/custom-plotting/README.md) |
| Coordinate GUI and terminal sessions | [Session coordination](workflows/session-coordination.md) | Session templates; optional [Herdr guide](clients/herdr.md) |
| Resume interrupted or remote work | [Remote work](workflows/remote-work.md) | Session templates |

Browse the [handbook](handbook/README.md) for how the pieces fit. The agent
instructions live in `skills/`; procedures live in `workflows/`; executable
checks live in `scripts/`. Reading an instruction does not install a check.

## Bring selected pieces into your project

Clone this repository, inspect a skill and its linked dependencies, then copy
the selected files into your project or link to your local checkout. Preserve
relative reference files inside a skill directory. For skills that link to
`workflows/` or `templates/`, retain those relative paths or update the links to
your chosen locations. Explain the selected locations in your project instructions.

Copied files are yours to adapt; updates do not merge themselves into your edits.
Record the upstream commit when copying. If using a checkout directly, review
updates before changing the version used by an active study. Do not install both
a copied and linked version of the same skill.

See setup guides for [Codex](clients/codex.md), [Claude Code](clients/claude-code.md)
and [OpenCode](clients/opencode.md). Fresh-client runtime verification is recorded
separately from documentation checks. This repository does not depend on a particular
model subscription. Choose tools and review effort for the concrete task.

## Plotting and group extensions

[analyb](https://github.com/jtavizon98/analyb) is the supported plotting
dependency in the [two-renderer example](examples/custom-plotting/README.md).
Its requirements file pins the reviewed public snapshot used for local checks;
a clean-environment installation check remains pending. Other plotting libraries are welcome:
the [integration companion](workflows/plot-evidence.md) describes the evidence
the review process needs without requiring a particular visual style.

The private [atlas-agents](https://gitlab.cern.ch/jtavizon/atlas-agents) extension
will hold group computing and ATLAS procedures. Nothing here should require
access to it. Personal phone relays and machine inventories are excluded.

## Reuse and provenance

First-party material is [MIT licensed](LICENSE). Retain the
[third-party notices](THIRD_PARTY.md) when copying adaptations. Source provenance
and the scope of publication are reviewed independently of the license choice.
