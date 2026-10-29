# Scientific agents

Agent skills for scientific research: settle decisions before building, read
sources and keep one citation library, write scientific code whose reasoning
can be checked, design figures and reports, review the rendered result, and
hand work between sessions without losing its evidence.

These are the skills I use for my own thesis work, maintained here so that my
setup and this repository stay the same thing. Take what helps, change it for
your project, and leave the rest. You do not need to reorganize your project or
use every skill.

## Skills

| Skill | Use it to |
| --- | --- |
| [grilling](skills/grilling/SKILL.md) | Settle the decisions a plan depends on before implementing it |
| [source-discovery](skills/source-discovery/SKILL.md) | Find and read sources, including through a signed-in browser session |
| [source-library](skills/source-library/SKILL.md) | Keep one BibTeX library and claim-level citations across reports |
| [scientific-coding](skills/scientific-coding/SKILL.md) | Write or reconstruct scientific code as readable, validated stages |
| [scientific-plotting](skills/scientific-plotting/SKILL.md) | Design figures and plotbooks around what the reader must decide |
| [plotting-integration](skills/plotting-integration/SKILL.md) | Make your own plotting library emit evidence the review checks can use |
| [report-writing](skills/report-writing/SKILL.md) | Plan, write, build and review a substantial report |
| [render-review](skills/render-review/SKILL.md) | Check a rendered PDF mechanically, then scope a visual review |
| [session-coordination](skills/session-coordination/SKILL.md) | Delegate, hand off and recover work across sessions and machines |
| [long-job-continuation](skills/long-job-continuation/SKILL.md) | Wait for Slurm, PanDA or other long jobs without a polling agent |
| [unblocker](skills/unblocker/SKILL.md) | Keep an agent moving through usage limits and waits while you are away |
| [wizard](skills/wizard/SKILL.md) | Walk a person through steps only a human may do, such as credentials |
| [workspace-lifecycle](skills/workspace-lifecycle/SKILL.md) | Sweep leftover worktrees and builds, and close out a study |
| [unslop](skills/unslop/SKILL.md) | Remove AI tells from writing while keeping scientific precision |

Each skill folder is self-contained: `SKILL.md` for the agent, `references/`
for the detailed procedures, `scripts/` for the checks it runs. Skills refer to
each other as `../<skill>/SKILL.md`, so keep related skills side by side.
Reading an instruction does not install a check; the scripts do the checking.

The [handbook](docs/guide/README.md) explains how the pieces fit for a person
reading it, not an agent.

## Install

**As a plugin** (Claude Code or Codex), updated with this repository:

```bash
claude plugin marketplace add jtavizon98/scientific-agents
claude plugin install scientific-agents@scientific-agents
```

```bash
codex plugin marketplace add jtavizon98/scientific-agents
codex plugin add scientific-agents@scientific-agents
```

Claude Code prefixes plugin skills, so `grilling` becomes
`scientific-agents:grilling`.

**By copying**: clone the repository and copy the skill folders you want into
your client's skill directory (see [Codex](docs/clients/codex.md),
[Claude Code](docs/clients/claude-code.md), [OpenCode](docs/clients/opencode.md)).
Copied files are yours to edit; record the commit you copied from, and merge
upstream changes by hand. Pick one route per client, or you get every skill twice.

The scripts need Python 3.10 or newer. The render checks need PyMuPDF and a TeX
installation; citation checks need Biber. Install them in your project's
environment, not in the system Python.

## Plotting

[analyb](https://github.com/jtavizon98/analyb) is the plotting library these
skills support out of the box. Other plotting libraries work too: the
[integration skill](skills/plotting-integration/SKILL.md) describes the evidence
the review checks need, and the [two-renderer example](examples/custom-plotting/README.md)
shows the same checks with Matplotlib and with analyb.

## Reuse and provenance

First-party material is [MIT licensed](LICENSE). Keep the
[third-party notices](THIRD_PARTY.md) when you copy adapted skills.
[MIGRATION.md](MIGRATION.md) records what has been checked and what has not.
