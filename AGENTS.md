# Maintaining scientific-agents

This repository contains adaptable scientific workflows, not a required project
layout. Read README.md and the workflow owning the behavior before editing.
Keep skills small; link detailed procedures and declare dependencies. A copied
skill must not silently depend on its author's private workspace.

For workflow changes, trace the rule through skills, procedures, examples,
scripts, tests and the handbook. Change the owner first and remove superseded
instructions. Distinguish prose guidance, explicit preflight and automatic checks.
Test omitted inputs and interrupted/recovery paths when changing enforcement.

Use synthetic or redistributable examples with recorded provenance. Never add
credentials, private research, raw agent transcripts or restricted source copies.
Do not invent citations, metadata or test results. Preserve existing user changes.
Keep scientific definitions in their analysis owner; plotting tools should not
silently choose normalization, covariance or scientific acceptance criteria.

Use the project's Python environment for tests; do not install into system Python.
Publication and local implementation are separate actions. Review exact staged
content and target before publishing. No force-push as incidental maintenance.

## Rules and what enforces them

Maintained with the [correct](skills/correct/SKILL.md) skill. A rule with no
enforcer that is broken twice gets one.

| Rule | Enforced by |
| --- | --- |
| A skill's `name` matches its folder and it has a description | `tools/check_repo.py` (CI) |
| Relative Markdown links resolve | `tools/check_repo.py` (CI) |
| An adapted skill keeps its upstream licence file | `tools/check_repo.py` (CI) |
| Adapted skills follow upstream changes by review, never silently | `tools/check_upstream.py`, weekly issue (`.github/workflows/upstream.yml`) |
| Scripts keep their tested behavior | `pytest` (CI); TeX-dependent tests run locally only |
| A rendered PDF is checked before visual review | `render_gate.py gate` in render-review |
| Credentials, private research and transcripts stay out | review before publication (no automatic check) |
