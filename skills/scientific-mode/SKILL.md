---
name: scientific-mode
description: Entry point for non-trivial scientific work. Restates the goal, picks a playbook, copies its steps into the todo list and routes to the other skills as the steps need them. Use for /scientific-mode, or when the project's instructions make it the default.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/poteto-mode/SKILL.md
  adapted-for: scientific work
---

# Scientific mode

Sibling skills live at `../<name>/SKILL.md` from this file. Put this file's
path in every delegate brief so the delegate reads it too.

## Start

1. In your first message, state in your own words the goal, the question the
   work answers and the smallest deliverable that meets it. Do not wait for
   confirmation. If the evidence rules out what was asked, show the evidence
   and stop. Restate the goal in every delegate brief and in the final reply
   (see [The reply](#the-reply)).
2. Pick a playbook below. Open a todo list whose first items are its steps,
   copied word for word. A step you skip stays in the list as
   `skip: <reason>`. If no playbook fits, write a short one in the same form in
   the session `STATE.md` and follow it.
3. Before changing a workflow or policy, the design of an analysis, several
   repositories at once, or a substantial report, run
   [grilling](../grilling/SKILL.md) and get its decision record confirmed.
   Routine and local work needs no such pass.
4. Decide, record, report: proceed on reversible work and on defensible
   scientific defaults, record each default, and keep dependent results
   awaiting review. Gated actions keep their gates. See
   [consequential actions](../session-coordination/references/consequential-actions.md).

## Playbooks

- **Study and comparison** ([playbook](playbooks/study-and-comparison.md)): a
  new study, validation or reproduction; comparing processings, versions or a
  reference result.
- **Discrepancy hunt** ([playbook](playbooks/discrepancy-hunt.md)): two
  results that should agree do not, and the cause must be found.
- **Figures and reports** ([playbook](playbooks/figures-and-reports.md)):
  designing or revising figures, a plotbook or a report, including a round of
  feedback.
- **Pickup, pause and cleanup** ([playbook](playbooks/pickup-pause-cleanup.md)):
  resuming another session's work, stopping work so it can resume cleanly, and
  closing out a study.

Long jobs go straight to [long-job-continuation](../long-job-continuation/SKILL.md);
work that must continue while the user is away goes to
[unblocker](../unblocker/SKILL.md).

## Routing

| When a step needs | Use |
| --- | --- |
| Understanding code, a method or a result | [teach](../teach/SKILL.md) |
| Independent review of a scientific conclusion | [council](../council/SKILL.md) |
| Sources, papers, protected pages | [source-discovery](../source-discovery/SKILL.md), [source-library](../source-library/SKILL.md) |
| Scientific code or a rewrite | [scientific-coding](../scientific-coding/SKILL.md) |
| Figures and plotbooks | [scientific-plotting](../scientific-plotting/SKILL.md), [plotting-integration](../plotting-integration/SKILL.md) |
| A report or rendered PDF | [report-writing](../report-writing/SKILL.md), [render-review](../render-review/SKILL.md) |
| Delegation, handoff, push, delivery, deletion | [session-coordination](../session-coordination/SKILL.md) |
| Leftover worktrees and builds, close-out | [workspace-lifecycle](../workspace-lifecycle/SKILL.md) |
| Any prose, including your reply | [unslop](../unslop/SKILL.md) |
| A task that taught something | [reflect](../reflect/SKILL.md) |
| The same correction a second time | [correct](../correct/SKILL.md) |

## Principles

Read the principle's skill in full before you apply it, and name it in your
reply with the choice it changed.

- [Explain the number](../principle-explain-the-number/SKILL.md): before you
  measure, and before you trust, report or act on a measured value.
- [Attack the premise](../principle-attack-the-premise/SKILL.md): when two
  fixes have failed the same check.
- [Fix root causes](../principle-fix-root-causes/SKILL.md): when debugging
  or chasing a discrepancy.
- [Build the lever](../principle-build-the-lever/SKILL.md): before doing or
  checking non-trivial work by hand.
- [Prove it on the real artifact](../principle-prove-it-on-the-real-artifact/SKILL.md):
  before you call anything done.
- [Prototype, don't ask](../principle-prototype-dont-ask/SKILL.md): before
  you ask the user a question a cheap run could answer.

## The reply

- Open with the goal, then what changed for the reader of the result.
- Give each claim its evidence or its label in the same sentence: measured,
  inferred or guessed. Never hand the user a check you could run.
- List the agent defaults taken and everything waiting on the user, each
  decidable from the reply alone.
- After work the user did not follow, reply with [ketchup](../ketchup/SKILL.md);
  its opening takes the place of the goal line above.
- Link only artifacts you produced or read in this session.
