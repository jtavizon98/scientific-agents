---
name: teach
description: Explain code, a method or a body of work so the user understands it, not only where it stands. Use for "teach me", "how does X work", "walk me through", code walkthroughs before changing something, or preparing to explain the work to someone else.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/teach/SKILL.md
  also-source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/how/SKILL.md
  adapted-for: scientific work
---

# Teach

Explain what a thing is, how it works and why it is built that way, in one plain account at the person's pace. The goal is that they understand it. Change nothing.

1. **Pick what they should leave understanding.** Choose a few points from why they ask (about to change it, review it, debug it, present it, write about it) and what they already know, both read from the conversation. Skip what they plainly know. Put the depth where the question is.
2. **Find out how it works before explaining.** Read the code, configuration or document yourself. For a subsystem across many files, delegate read-only exploration of two to four slices and combine the findings. Read what actually ran (the release, the configuration, the log), not only what the documentation says.
3. **Find out why only as far as the question needs.** Reasons come from sources: the commit, the merge request, the recommendation page, the paper, the decision record. Use [source-discovery](../source-discovery/SKILL.md), including its signed-in browser route for sources behind a login. Say how sure you are and why: a hedge is a finding, not style. "The commit message says X" and "this looks like X" are different claims.
4. **Start with a plain definition.** Name the thing and say what it is in general terms, with its common name if it has one. Then tie it to the case at hand ("here it decides which jets count as b-tagged") and build up: the problem it solves, how it works, the edge cases. Walk through what happens to one event, one file or one call when that makes it land. A list of functions and constants is reference, not teaching.
5. **Give the smallest complete answer first,** a sentence or two, then stop. Add layers when they ask. Never a wall of text.
6. **Build pictures up.** For three or more moving parts, draw a short series where each diagram redraws the last and adds one part, so the reader watches the system assemble. For a physics quantity, write the equation and name each term before the code that computes it. A single simple point needs no figure.
7. **Keep it a conversation.** No quizzes, no "pause here", no announcing that a part is important or hard. When you would pause, stop and let them respond. Without a live reader, deliver it cleanly and end with the threads worth following.

For a code walkthrough kept in the project's notes or documentation, use these sections and drop the ones that do not apply: overview, key concepts, how it works, where things live, gotchas.

Write through [unslop](../unslop/SKILL.md). Give each concept one name and keep it. State the mechanism, not a metaphor for it.

**Reply:** the explanation itself, not a report about it.
