# Workspace Lifecycle

Sessions record what they leave behind; one command sweeps it. Reversible
cleanup runs without per-item approval. Everything else is listed for the approver.

## When

Sweep on demand and at study close-out. At close-out, fill `## Leftovers` in
`RESULT.md` ([template](../../session-coordination/references/templates/RESULT.md)), run a dry run, and
quote its summary in the handoff.

## Command

```bash
python3 <skill-dir>/scripts/workspace.py sweep                    # dry run
python3 <skill-dir>/scripts/workspace.py sweep --apply            # autonomous actions
python3 <skill-dir>/scripts/workspace.py sweep --apply --settle-sessions
python3 <skill-dir>/scripts/workspace.py sweep --apply --approve REPORT_SHA256
```

`<skill-dir>` is the installed skill folder. Run from the project root, which
holds your own `lifecycle/topology.json` (copy and adapt
[the example](topology.example.json) first, then run `validate-manifest`); relative paths in the
topology (`sessions`, `.lifecycle`) are resolved against it. Set
`AGENT_SESSIONS_DIR` to use a different sessions folder.

Each run writes a new `.lifecycle/sweep-<UTC>-<pid>-<rand>.json` and `.md` (add `.lifecycle/` to `.gitignore`).
The host comes from the hostname or project root in
`lifecycle/topology.json` (override with `--manifest`); `--local-host` overrides it. The sweep reads
only local paths: registered repositories, their worktree lists, the topology
`worktree_roots`, and `## Leftovers` paths; its only network call is the
`git ls-remote` check below. Other hosts are not swept. A failed Git query
makes the item `needs_owner`, and an oversized tree is `too_large`; neither
aborts the sweep.

## Autonomous with `--apply`

A linked worktree is removed with `git worktree remove` (never `--force`) only
when all of these hold; otherwise it is `kept` or `needs_owner`:

- it is not a registered repository, the project root, `$HOME`, or an
  ancestor of one, and its real path lies inside a `worktree_roots` entry with
  no symlink component;
- no open session names it (status not complete, closed, or superseded, or a
  pending review, or a live owner), and it is not locked;
- status shows no tracked change and no untracked file, `git ls-files -v`
  shows no assume-unchanged or skip-worktree flag, and every ignored entry is
  a `*.pyc`/`*.pyo` file, a `__pycache__/` holding only those, or a
  `.pytest_cache/` holding only `.gitignore`, `CACHEDIR.TAG`, `README.md`, and
  `v/cache/{lastfailed,nodeids,stepwise}` (no symlink, no nested `.git`);
- it is on a branch, idle for `minimum_age_days` (30), and a live
  `git ls-remote` (batch mode, no prompts, 30 s timeout) shows the branch tip
  exists locally and contains HEAD. Stale tracking refs, `remote = .`, and a
  remote URL pointing back at the same repository never count.

Its local branch is then deleted with `git branch -d`; if Git refuses, the
branch stays.

`--settle-sessions` needs the user's confirmation first. It settles a session with
`RESULT.md`, a closed status, no pending review, no live owner or delegated
job, 30 idle days, the same status, flag, and ignored-entry conditions, and
no `unique-never-delete` leftover or `keep-until-review` leftover whose target
still exists (settling would drop that protection). Settling never deletes
untracked content: it stages `git rm -r` (no `-f`), removes the folder only if
it is then empty, and appends one row to `sessions/ARCHIVE.md`
(created on first use). The coordinator commits.

An unreadable session record counts as an open session that protects every
path, and is reported. Protection follows directories, compared by path component and inode. A
`unique-never-delete` leftover, a `keep-until-review` leftover of an open
session, or an open-session mention of a path, of a directory below it, or of
an ancestor inside a configured root protects that path, everything below it,
and every ancestor that contains it. Registered checkouts and the project root
protect themselves, their ancestors, and their contents (inventoried artifacts
excepted); `$HOME` and storage tiers protect themselves and their ancestors.
This applies to removal, settling, and approved deletions. A session that lists
an exact path as a `disposable-once-pushed` leftover does not protect that path
through its own mention; other open sessions' mentions still do.

Every action reclassifies its target with freshly read
session records and skips it on any change. `--apply` runs hold `.lifecycle/sweep.lock`
until the report is written; report names carry UTC microseconds, the pid, and
a random suffix; each is fsynced to a temporary file and hard-linked into
place, so it is never overwritten. `--approve` skips malformed report files.

## Approval

Dirty, untracked, unpushed, unregistered, or non-Git items are `needs_owner`.
Rebuildable untracked artifacts and `disposable-once-pushed` leftovers of
closed sessions are `needs_approval` when they are small (at most 10,000
entries and 64 MiB, fingerprinted by content SHA-256, inode, mode, and size)
and contain no symlink component, no Git-tracked path, and no nested
repository, and when no session protects them (`unique-never-delete`,
`keep-until-review` while open, or a mention by an open session). The approver (the topology `approver` field; by default the project owner) approves them all at once by handing
back the report hash; record it in the active `STATE.md`. `--approve` then
reclassifies everything and deletes only items still `needs_approval` with an
unchanged fingerprint, alongside the usual autonomous actions.

## Restore

- Worktree: `git -C <repo> worktree add <path> <branch>`, or
  `-b <branch> origin/<branch>` when the local branch was deleted.
- Session: `git checkout <restore commit> -- sessions/<name>` from the
  project root.

## Verification

```bash
python3 <skill-dir>/scripts/workspace.py validate-manifest
python3 -m pytest tests/test_workspace.py -q -p no:cacheprovider
```
