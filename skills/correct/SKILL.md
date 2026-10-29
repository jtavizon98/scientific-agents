---
name: correct
description: Use when the same mistakes keep recurring in a repository, to make the next agent unable to repeat them by changing structure, checks and tests before wording.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/correct/SKILL.md
  adapted-for: scientific work
---

# Correct

The same mistakes keep getting corrected. Change the repository so the next agent cannot make them.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example and takes the shortest path that works. A change that looks right from one file should be right for the whole repository.

## Find the mistake classes

Read recent commits, reverts, review files, session records (`STATE.md`, `RESULT.md`), instruction files, comments that explain workarounds, and the harness's memory or notes if the user keeps any. Group the mistakes into classes. A class counts once it has happened twice.

## Fix each class at the highest level that works

1. **Eliminate it by structure.** One owner per quantity and one supported way per task: one config for the luminosity or normalization, one function that applies weights, one source for a list that was kept in sync by hand. Delete old scripts and dead paths an agent would copy.
2. **Enforce it with a check whose error names the fix.** A validation assertion in the analysis code (weights present, sample list complete, units declared), a render gate or source check that fails the build, a lint rule. Name the file or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** A unit test on synthetic data with a known answer. Fix or delete any test that still passes when the behavior breaks, or fails when only internals change.
4. **Write instruction text last,** only for judgment calls. Nothing fails when an agent skips it.

## Fix and prove

Fix the most frequent classes now, one commit each, and prove each new check fails on a real past mistake. Run the same command wherever it is enforced. Exceptions go on the offending line with a reason and the human's approval. Changes that alter workflow follow [workflow changes](../session-coordination/references/workflow-changes.md); decisions the human must make go through [grilling](../grilling/SKILL.md).

## Keep the rule table

Keep a table in the project's agent instruction file or its personal overlay (for example `PERSONAL.md`) pairing each rule with what enforces it:

| Rule | Enforced by |
| --- | --- |
| Cutflow weights are applied from the first cut | assertion in the cutflow function |
| Built report passes the render gate before review | the render check |

When the human corrects you, fix the mistake and add the rule. If the rule already existed and nothing enforced it, that is a repeat: fix it at the highest level in the same change. Drop a rule once its mistake cannot happen.

**Reply:** each class with its evidence, the level you chose, and why a higher level did not work.
