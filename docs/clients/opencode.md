# OpenCode V2

Documentation checked 2026-10-28:
https://opencode.ai/v2/docs/skills

OpenCode discovers `.opencode/skills/`, with compatibility discovery for
`.agents/skills/` and `.claude/skills/`. It also supports those user-level
compatibility locations and `~/.config/opencode/skills/`.

For selective adoption, copy a chosen skill directory to `.opencode/skills/`
and retain or adapt its linked dependencies as described in the README. Do not
install another same-ID copy in a compatibility location.

To expose **all included skills** from a maintained checkout instead, V2 can add
its skills directory directly to the project's existing configuration:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["/absolute/path/to/scientific-agents/skills"]
}
```

Merge the selected entry; do not replace an existing configuration wholesale.
Relative skill-source paths resolve from the active working directory, not the
configuration file, so an explicit local path avoids surprises when working in
subdirectories. Personal absolute paths belong in local configuration, not shared
project files. Explicit skill sources have higher precedence than ordinary
discovery; inspect duplicate IDs before relying on an override.

Invoke `@source-library` and ask the agent to identify the skill's base directory
and read its linked workflow. Permissions can hide or block a skill; inspect
the selected agent's rules rather than granting blanket access. Supporting files
are not loaded merely because the skill is listed.

## Registering `monitor_wait`

Skill discovery does not register the `monitor_wait` tool used by
[long-job-continuation](../../skills/long-job-continuation/SKILL.md). It comes
from an OpenCode plugin, `skills/long-job-continuation/scripts/opencode-monitor-wait.ts`.

1. Copy the file, or symlink it, into `.opencode/plugins/` of the project. It
   imports `@opencode/plugin` and runs `python3` (3.10 or newer) on
   `monitor_wait.py`, which it looks up next to itself; set
   `MONITOR_WAIT_SCRIPT` to the path of another copy if you copied only the
   plugin.
2. Restart OpenCode so it loads the plugin. The plugin was extracted from a
   working setup and is not covered by tests here; check it against your
   OpenCode version.
3. Check that `monitor_wait` appears in the agent's tool list before relying on
   it. If it does not, treat the tool as unavailable.

The tool runs a local process that reads and writes under the project's
`sessions/` folder, so it needs the same read and write permission as any other
local command in that folder.

Status: instructions checked against V2 documentation; isolated fresh-client
runtime discovery is pending. No active server or global configuration is changed
by this guide.
