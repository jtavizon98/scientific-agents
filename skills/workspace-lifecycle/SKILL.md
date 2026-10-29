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

3. Add `--settle-sessions` only after the user has confirmed session settling.
   It settles only folders without untracked content, stages `git rm -r`, and
   appends `sessions/ARCHIVE.md`; the coordinator reviews and commits.

4. Show the approver (the topology `approver` field, by default the project
   owner) the `needs_owner` and `needs_approval` lists. Delete `needs_approval`
   items only after they hand back the report hash:

   ```bash
   python3 <skill-dir>/scripts/workspace.py sweep --apply --approve REPORT_SHA256
   ```

At study close-out, fill `## Leftovers` in `RESULT.md` (template in
[session coordination](../session-coordination/references/templates/RESULT.md))
before the dry run. Never edit the topology file to make a finding disappear;
add a worktree root or repository only when the layout really changed.
