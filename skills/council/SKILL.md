---
name: council
description: Independent review by one strong model from each reachable provider, in parallel, with verdicts, a two-round limit and a recorded result. Use when the user says "council", and for the required independent review of a physics, statistical or numerical conclusion.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/t3dotgg/tstack/blob/1085050/skills/council/SKILL.md
  adapted-for: scientific work
---

# Council

Bring in one reviewer per model provider, so that a blind spot shared by one model family does not pass review unseen.

## Before the review

Fix what you already know is wrong and run the checks that apply (tests, the render gate, the source check). Give the council the updated work. Do not hold known fixes back until reviews return. If the user wants to discard the work and explore alternatives, skip fixes to what will be replaced.

## Members

Use the members and efforts the project's settings name. Without them, use the strongest model of each provider you can reach at high reasoning effort or above, and name the choice in the record. Use the harness's subagents, or the route the project's settings name for providers the harness does not expose. A fresh session of the author's own model family counts as a member; the author's session does not. If a provider or a named member cannot be reached, say so in the result. Never fill the seat with another model.

## The brief

Give every member the same self-contained brief: the question the work answers, the artifact or diff, the evidence it rests on, and the decisions already settled that are not under review. Give them the work, not your conclusion about it. Members work read-only and do not see each other's reviews.

Ask each for:

- a verdict: accept, accept with changes, or reject;
- findings that stand only if a run or calculation shows them, or if they name the exact missing assumption;
- risks, listed apart from findings;
- for a conclusion, what evidence would change their verdict.

## Rounds

One full review pass by every member is one round. Collect the verdicts, then summarize the findings, where members disagree, and the next steps. Make the changes you agree with, record why you reject the others, and run a fresh round on the updated work. Tell members which earlier findings were fixed or rejected and why.

Stop reviewing when every member accepts, or after the second round. What is still open then is handled by kind:

- A finding (shown by a run or calculation, or naming an exact missing assumption) is fixed, or the claim it touches is withdrawn or marked unsupported. It never becomes a default. A finding you rejected that a member still upholds after the second round stays open unless a run or calculation in the record refutes it.
- A disagreement of judgment that no run can settle: if it would change a scientific claim, ask the user; otherwise take a default, record it under "Agent defaults (unreviewed)" in `STATE.md` and continue ([decide, record, report](../session-coordination/references/consequential-actions.md#decide-record-report)).
- Gated actions keep their gates whatever the reviews say.

Keep the scope fixed. A finding outside the question under review goes to the leftovers, not into this round.

## Record

Put the result in `RESULT.md`, and in the report's review record when there is one:

```markdown
## Council review

Question: <what was reviewed>
Rounds: 2
Missing: <provider not reachable, or none>

| Member | Round 1 | Round 2 |
| --- | --- | --- |
| <model, effort> | accept with changes | accept |
| <model, effort> | reject | accept with changes |
```

Write "no verdict" when a member gives none; never invent one. A council does not replace the human domain review the project requires.
