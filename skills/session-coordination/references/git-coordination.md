# Git coordination

Git remotes are the source of truth. Git is also the normal machine-handoff
mechanism. Synchronize when ownership or review needs to move; do not maintain
continuous lockstep between otherwise independent checkouts.

## Start a writing task

1. Identify the owning repository and read its instructions.
2. Inspect `status -sb`, branches, worktrees, and remotes.
3. Assign one owner, branch, and worktree for the task by default.
4. Record the checkout and starting commit in session state.

## Update safely

Pull manually rather than from cron. Fetch only when remote access is
intended, inspect divergence, then fast-forward when safe. Never silently
reset, force-push, overwrite, or merge around unknown work.

## Commit and hand off

- Keep commits coherent and small enough to review.
- Stage explicit paths and review the staged diff.
- Record verification and remaining gaps in `RESULT.md`.
- Push only with explicit publication intent and correct content
  classification for the destination.
- Confirm the remote commit after pushing.
- Commit and push unique edits before leaving them on scratch storage or a
  deployment copy. Never edit code through a network mount or an SSH session
  that is only a deployment copy.

Parallel software changes and overlapping document edits use separate
worktrees. A shared coordination checkout may be used when sessions own
non-overlapping state paths, one integrator owns staging and publication, and
every participant preserves unknown dirty state. If two tasks need the same
report or policy file, serialize them or appoint one writing owner. The user
may override this default for a specific coordinated task.

## Material you must not publish

A private remote is not blanket approval. Do not add confidential, embargoed or
collaboration-internal text until its classification and the repository's
suitability are explicitly approved. Prefer a provenance pointer when copying
source material is unnecessary. Never stage credentials, tokens, certificates,
harness transcripts or personal material.
