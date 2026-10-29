---
name: grilling
description: Use when the user asks to grill or stress-test a plan, decision, or idea, or when project instructions require a pre-implementation decision pass. Inspects facts, resolves dependent decisions in rounds, and requires a confirmed decision record.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/mattpocock/skills/blob/a496f55/skills/productivity/grilling/SKILL.md
  adapted-for: research projects and consequential-work boundaries
---

# Grilling

Run a read-only alignment pass before implementation. Confirmation of the
result means the plan is understood; it does not authorize a push, publication,
remote operation, destructive action, credential change, or other
consequential step.

## Establish the decision tree

1. Read the relevant repository instructions, owning documentation, current
   state, and existing implementation before asking questions.
2. Separate facts the environment can answer from decisions the user owns.
   Investigate facts directly or delegate bounded read-only exploration to a
   subagent with a fresh context; never ask the user to retrieve information
   available to the agent. If a cheap run can show the answer to a fork, run it
   instead of asking ([prototype, don't ask](../principle-prototype-dont-ask/SKILL.md)).
3. Map decisions by dependency. A decision enters the current frontier only
   when its prerequisites are settled.
4. Keep only choices that materially affect scope, behavior, architecture,
   interfaces, risk, evidence, validation, rollout, or recovery. Resolve normal
   implementation details using established project conventions. Grilling is
   for plans whose gate applies; a scientific choice met during ordinary work
   follows [decide, record, report](../session-coordination/references/consequential-actions.md#decide-record-report).

## Work the frontier

Ask the whole current frontier in one round, then wait. Use the harness's
structured question tool when it has one: give each question real alternatives,
put the recommended answer first and state its consequence. When questions
travel through a text relay, such as a phone thread, number them instead and
word each one so "yes" accepts the recommendation. Allow a free-form answer
when the alternatives are not genuinely closed. A question that depends on an
unsettled answer belongs to a later round.

After each response, update the tree, reconcile contradictions with earlier
answers, and ask the next frontier. Do not repeat settled questions unless new
evidence invalidates their premise.

Do not manufacture ambiguity. If inspection shows that the user has already
specified every material decision, skip directly to the decision record.

## Confirm the decision record

When the frontier is empty, present one concise record containing:

- settled decisions;
- scope and explicit non-goals;
- assumptions and supporting evidence;
- affected owners, repositories, interfaces, or artifacts;
- implementation sequence;
- verification and acceptance criteria;
- rollout and recovery where applicable;
- unresolved blockers.

Ask the user to confirm or correct that record. Do not begin implementation
until they confirm it. If they correct it, reopen the affected branches and
continue the interview.

Plan confirmation does not replace a repository's authorization workflow,
independent review, source verification, physics or numerical validation, or
human domain approval.

## Carry the contract into the artifact

Before implementation and at substantial handbacks, check the planned or
produced artifact against the confirmed audience, intended use, reference
artifacts and prior contracts, exclusions, and concrete acceptance examples.
Retrieve any relevant earlier standard before improvising a replacement. If a
material requirement is missing or conflicts with the result, resolve that gap
with the owner; do not treat a nearby deliverable as completion. This check does
not add a questioning pass to genuinely routine work.
