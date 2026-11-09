---
name: workspace-lifecycle
description: Sweep a project workspace for leftover worktrees, rebuildable artifacts and settled sessions, and close out a study. Reversible removals are autonomous; other deletions need the designated approver's report-hash approval. Use for cleanup, leftover worktrees, study close-out, or settling old sessions.
---

# Workspace lifecycle

Policy: [workspace lifecycle](references/workflow.md). Run from the project
root on the host that owns the paths. The script lives in the installed skill,
so the commands below use `<skill-dir>`, the folder that holds this
`SKILL.md`. The tool detects the host from the topology file in your project
(default `lifecycle/topology.json`; see [the example](references/topology.example.json)
and [schema](references/topology.schema.json)).

First run in a project:

1. Copy the example to `lifecycle/topology.json` in the project root and adapt
   it: the real host name or project root, your repositories, the
   `worktree_roots` where linked worktrees may live, and the `approver`.
2. Validate it before any sweep:

   ```bash
   python3 <skill-dir>/scripts/workspace.py validate-manifest
   ```

Each sweep:

1. Dry run and read the summary it prints:

   ```bash
   python3 <skill-dir>/scripts/workspace.py sweep
   ```

2. If the `remove` list looks right, apply the autonomous actions:

   ```bash
   python3 <skill-dir>/scripts/workspace.py sweep --apply
   ```

   This removes only clean, idle linked worktrees inside the configured roots
   whose branch a live `git ls-remote` confirms, rechecking each one first. It
   never uses `--force` or `git branch -D`.

3. Add `--settle-sessions` only after the user has confirmed session settling,
   once or as a standing project setting. It settles only folders without
   untracked content, stages `git rm -r`, and appends `sessions/ARCHIVE.md`;
   the coordinator reviews and commits.

4. Show the approver (the topology `approver` field, by default the project
   owner) the `needs_owner`, `needs_approval`, `reclaim` and `stale_review`
   lists. Delete `needs_approval` items and closed sessions' `reclaim` build
   output, and close `stale_review` sessions, only after they hand back the
   report hash:

   ```bash
   python3 <skill-dir>/scripts/workspace.py sweep --apply --approve REPORT_SHA256
   ```

At study close-out, settle the study's branches (merged ones deleted, unmerged
work archived; see [workflow](references/workflow.md#when)) and fill
`## Leftovers` in `RESULT.md` (template in
[session coordination](../session-coordination/references/templates/RESULT.md))
before the dry run. Copy any record a study document cites into that study's
evidence folder and cite it there
([source hierarchy](../report-writing/references/report-production.md#source-hierarchy)):

```bash
python3 <skill-dir>/scripts/workspace.py cite-evidence --session NAME --dest STUDY_EVIDENCE_FOLDER
```

The dry run lists the copies, the rewritten citations and anything left for
the owner; `--apply` copies (tracked files as committed), writes
`PROVENANCE.md` and rewrites the citations in the working tree, staging
nothing. The sweep never settles a session that a tracked file outside the
sessions folder still cites. Never edit the topology file to make a finding disappear;
add a worktree root or repository only when the layout really changed.
