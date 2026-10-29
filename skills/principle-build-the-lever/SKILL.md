---
name: principle-build-the-lever
description: Apply to any non-trivial edit, migration, comparison or check. Build the script that does the work or proves it instead of doing or checking it by hand.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/principle-build-the-lever/SKILL.md
  adapted-for: scientific work
---

# Build the lever

When the work is not trivial, build the tool that does it instead of doing it by hand.

A script does the work the same way every time and reruns for free. It is one artifact a reviewer can read and rerun to check the work; a number read off a plot by eye can only be rechecked by reading it again. A deterministic script turns "trust me" into "run this", which is what reproducibility asks for.

Skip it only when the task is a couple of obvious edits you can see at a glance.

- Do the first unit by hand to learn the recipe, then write the script. Prove it by rerunning it on that unit and comparing with your hand-done result. Make it safe to rerun.
- A script for edits across files, a generator for repetitive configuration, a query or table dump for a comparison, a rerunnable check for verification.
- A script that covers every unit in one pass beats fanning the work out to delegates who apply it by hand.
- When delegates must share a recipe, write it down once (recipe, verification and what not to touch) outside their write scope.
- Commit the script beside the result when the result outlives the session, and name it in `RESULT.md`.

The bar is triviality, not repetition: a one-off earns a script when the script is what makes the result checkable. Build the smallest script that does or proves the job, never a framework. For proving the produced output, see [prove it on the real artifact](../principle-prove-it-on-the-real-artifact/SKILL.md).
