# Session result: <name>

## Outcome

State whether the objective is complete, partial, blocked, failed, or awaiting
human review, and name the reviewable artifact. Separate observation from
inference.

## Changes and decisions

- `<path or commit>` - `<purpose>`
- **Observed:** `<verified fact>`
- **Decision:** `<accepted choice and owner>`
- **Proposal:** `<unapplied recommendation and owner>`

## Verification

| Check | Result |
| --- | --- |
| `<command/review>` | `<pass, fail, or unavailable>` |

## Remaining gaps

- `<not verified or not done, with reason>`

## Leftovers

One line per worktree, branch, scratch directory, or bulk output this session
created, or `- none`. Use an absolute path (or `repo@branch`) and one
disposition: `disposable-once-pushed`, `keep-until-review`, or
`unique-never-delete`. Cleanup is a separate action; a result does not
authorize deletion.

- `<absolute path or repo@branch>` `<disposition>` - `<what it is>`

## Handoff

- Starting and final commits: `<sha> -> <sha>`
- Dirty/untracked state: `<none or exact paths>`
- Classification: `<status>`
- Human review: `<not applicable | pending | accepted | superseded | closed>`
- Artifact and delivery: `<path, destination, time, result>`
- Blocker/completion notification: `<not requested or destination/time/result>`
- Next action: `<one action and owner>`

Do not imply a push, job action, delivery, notification, or acceptance without
direct evidence.
