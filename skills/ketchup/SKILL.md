---
name: ketchup
description: Catch the user up on what changed since their last message, in plain words, and list every call waiting on them so they can decide each from the reply alone. Use for /ketchup, when the user returns to unattended work, or when a relay or unblocker reports to the user.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/1ba91fc/pstack/skills/ketchup/SKILL.md
  adapted-for: scientific work
---

# Ketchup

Catch the user up on what changed since the last message they wrote before asking for the catch-up, and help them understand each change, not only where it stands. Then lay out every call waiting on them so they can make it from your reply alone. Notifications, subagent results and relay messages are not their messages. Assume the user remembers their last message and nothing after it.

## Gather

Catching up changes nothing: start no code changes, jobs, deliveries or posts for it. Sending the catch-up through the agreed relay route is allowed, and a caller that goes on working afterwards does so as its own step. Collect your own work since that message, delegate reports, and the current state of every branch, job, artifact and agent the work touched. Read the session's `STATE.md`, including its agent defaults. Check every number you will show against the output it comes from, and say so when you correct one.

A **call** is a step only the user can take: a scientific choice the evidence does not settle, an approval, an action behind a gate, or access you lack. Include every call still open, even one raised before their last message, and every unreviewed agent default together with the results that depend on it. Work you can still do yourself is not a call. Never invent a call to fill the reply.

For each call collect its pick, the evidence behind it, its risk, and what changes for the result or the reader. Write "unknown" for a fact the call needs that you do not have.

## Write

Open with one sentence that names what waits on the user, or says nothing does; the goal of the work, when needed, comes after it. If nothing happened and nothing waits, say so and stop.

Then what happened, in under 100 words when little happened: one line per thing the user asked for, saying what came of it and whether it is done, running, failed or not checked. Write each line the way you would say it aloud: "The yield gap was a missing trigger weight", not "Yield audit: done". Name any bug found and fixed on the way. Never mark something done that waits on the user.

Keep the numbers that are the result, each with what it measures and whether it was measured, inferred or guessed ([explain the number](../principle-explain-the-number/SKILL.md)). Leave out hashes, paths, commands and test counts unless the user needs one to act; they belong in `RESULT.md`. Translate every internal label (stage names, study codes, branch names) into what it is. When a figure shows the change, name the plotbook page to open instead of describing it at length.

Then the calls, about 30 words each, riskiest first:

- the call, your pick and what it changes for the result;
- the evidence behind the pick;
- the risk, even when low ("low risk: only the legend changes");
- what waiting costs, only when it is more than a delay.

When several items share one call, state the call and pick once, then one bullet per item. For a choice between options, give each option's gain and cost. Then one line naming the work left that you can do yourself.

Over a text relay to a phone, number the calls and word each so "yes" accepts your pick. Never shrink or drop calls to meet a word count.

Write through [unslop](../unslop/SKILL.md).
