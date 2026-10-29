# Changing workflows and instructions

Use this procedure when changing policies, workflows, skills, agent defaults or
their enforcing scripts. A skill-authoring helper can design and evaluate a
skill; this procedure checks consistency between surfaces. Scale the work to
the changed behavior rather than launching a general audit or benchmark for
every edit.

## Trace the rule before editing

1. Identify the canonical owner, intended behavior and concrete failure being
   repaired. Obtain whatever decision confirmation the project's instructions
   require.
2. Inspect current diffs and actual discovery paths, including symlinks. Preserve
   other owners' edits. Record shared versus project-local responsibility.
3. Trace direct consumers: root instructions, skills, workflows, templates,
   harness defaults/hooks, executable checks/tests and human guides. Search safe
   roots for the old requirement and its synonyms. Historical session evidence
   is history, not a surface to rewrite.
4. Record this small matrix in the existing session state:
   `rule | owner | consumers | enforcement | verification`.
   Distinguish automatic interception, explicit preflight and prose-only policy.
   Check default and omitted-argument behavior, not merely the documented happy path.

## Change one contract across its consumers

Update the owning rule first, then code and tests, skills and entry points, and
finally human guides. Remove superseded contradictory requirements rather than
appending another exception. Put detailed rules in one owner; entry points link
to it and state only the trigger and essential invariant.

Check that local instructions do not accidentally override shared routing or
authorization; that a tool's pass means what prose claims; and that optional
inputs cannot silently remove required coverage. Requirements for independence,
complete coverage and final delivery must not imply repeated identical work.

## Verify behavior and cost

Use focused deterministic tests and a few bounded instruction scenarios:

- normal work and a genuinely local revision;
- missing, stale or contradictory evidence;
- a global change versus harmless movement or repagination;
- interrupted work, quota failure and reuse of completed checks;
- model defaults, expensive escalation and termination after acceptance.

For review-policy changes, include an accepted large repetitive artifact with a
small edit. Check both under-review (missing evidence called PASS) and over-review
(all pages or expensive models selected without a concrete reason). Do not run
large model benchmarks or extra independent review merely to validate wording.
If model evaluation is needed, bound prompts, routes, calls and stopping criteria
in advance; use an economical suitable route.

Before handback, search active surfaces again for the removed rule, review diffs,
run affected tests, rebuild changed human guides and record exact gaps. State what
is actually enforced; a preflight command does not intercept arbitrary launches.
Record publication separately. Leave recovery instructions for owned dirty paths;
never reset shared files to undo only this task's changes.
