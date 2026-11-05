# Session state: <name>

- Status: `not started | in progress | blocked | paused | awaiting human review | complete | closed | superseded | failed`, optionally followed by `: <short note>`
- Review: `not applicable | pending | accepted | superseded | closed`
- Study: `<short label shared by every session of one study, such as daod>`
- Parent: `<none or the parent session's folder name>`
- Updated: `<ISO-8601 timestamp with timezone>`
- Control client: `<where the user or coordinator interacts>`
- Runtime/writing host and mode: `<observed hostname; plan or build>`
- Execution targets: `<none or exact hosts/services>`
- Owner: `<owner and native session ID>`
- Working copy: `<directory; branch/worktree @ sha>`
- Access boundary: `<allowed writes and preflighted external roots>`
- Consequence and authorization: `<level; exact action/target; who/source/time>`
- Jobs or delegated monitors: `<none or identifiers, owner, lease, handback>`
- Review artifact: `<none or paths>`
- Delivery and notifications: `<local/delivered evidence; blocker and completion signals>`
- Complete only when: `<end-to-end completion sentence>`

## Completed

- `<deliverable or checkpoint with evidence>`

## Agent defaults (unreviewed)

| Choice | Alternative | Reason | Evidence | Reversal |
| --- | --- | --- | --- | --- |

## Current observations

- **Observed:** `<fact and source>`
- **Inference:** `<interpretation>`
- **Proposal:** `<unapplied choice>`

## Verification

- `<command/check>` - `<result>`

## Blockers and gaps

- `<blocker, independent work remaining, and required owner>`

## Next safe action

`<one explicit action>`

## Resume and boundaries

Re-read the brief, this state, relevant ledgers, and the completion contract.
Reconcile current jobs and restore omitted validation, report, review, delivery,
notification, and publication todos. Repeat external-access preflight before a
new unattended delegation. Record a plan-to-build scope change before writing.

- Forbidden/not authorized: `<boundary copied from the brief>`

The workspace sweep reads the first five lines: an open session whose Status or
Review does not start with one of the listed values, whose Study is empty, or
whose Parent or `Supersedes` names no existing session is listed for its owner
to fix, and the generated `INDEX.md` beside the sessions is built from them.

If a handoff file is machine-read, map `in progress` and `awaiting human
review` to `in_progress`; map `blocked`, `paused`, `complete`, and `failed`
directly. `not started` has no handoff marker. Keep a report release held while
human review is pending.
