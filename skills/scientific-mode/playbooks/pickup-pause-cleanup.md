# Pickup, pause and cleanup

Use the part that applies. Details are in
[session-coordination](../../session-coordination/SKILL.md) and
[workspace-lifecycle](../../workspace-lifecycle/SKILL.md).

## Pickup

1. Read the session's `BRIEF.md`, `STATE.md`, `RESULT.md` and decision record.
2. Compare them with Git status, running processes and job state. Records can
   be stale; current evidence wins.
3. Confirm you are the only writer for the boundary. Never resume one native
   session from two clients.
4. When the user returns to work they did not follow, catch them up with
   [ketchup](../../ketchup/SKILL.md). Otherwise state the goal, the open agent
   defaults and the next safe action.
5. Continue.

## Pause

1. Stop at a checkpoint. Commit owned work, or record the dirty paths.
2. Update `STATE.md`: owner, exact source state, artifacts, live jobs and
   monitors, open agent defaults and the next safe action.
3. Hand waits to a monitor
   ([long-job-continuation](../../long-job-continuation/SKILL.md)), not to a
   polling agent.

## Cleanup and close-out

1. Run the workspace sweep as a dry run. Reversible removals of provably
   disposable items may proceed; every other deletion needs the approver's
   approval of the exact report.
2. Close the study: `RESULT.md` with what was shown, its review state and a
   `## Leftovers` list.
