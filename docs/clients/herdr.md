# Coordinating sessions with Herdr

Use Herdr when viewing and managing several agent sessions is useful. It is not
required to use the skills or to hand findings from a GUI session to a terminal.
Start with Herdr's [installation guide](https://herdr.dev/docs/install/) and
[quick start](https://herdr.dev/docs/quick-start/). After installation, launch
`herdr` from a project directory and run your installed agent in a pane. A Herdr
session is the background container for workspaces, panes and their running
processes; it is not an agent's native conversation ID. `YOUR_SESSION` below is
the explicit Herdr session name chosen for that container, created or attached
with `herdr --session YOUR_SESSION`. Remote use also needs an existing working
SSH alias and the documented remote installation.

Check the installed version's help before using control commands; examples below
describe the interface used by the source setup, not a guarantee for every release.

```bash
herdr --remote YOUR_SSH_ALIAS --session YOUR_SESSION
herdr --session YOUR_SESSION agent list
```

From an already Herdr-managed local session, bounded non-interactive inspection
or control may instead be forwarded through the authenticated SSH alias, one
command at a time:

```bash
ssh -o BatchMode=yes YOUR_SSH_ALIAS 'herdr --session YOUR_SESSION agent list'
```

Commands the [unblocker](../../skills/unblocker/SKILL.md) skill relies on:

```bash
herdr --session YOUR_SESSION agent read TARGET --source visible
herdr --session YOUR_SESSION agent wait TARGET --until idle --until done --until blocked --timeout 3600000
herdr --session YOUR_SESSION agent prompt TARGET 'message'
```

Run a wait as a background shell command so the harness wakes you when it
exits, keep its timeout at or below 3600000 ms (longer waits have lost their
completion notice), and wait for a state change, not the current state, which
returns at once.

Use the explicit named session: a default socket may refer to another server.
Inspect the agent list and recent output before prompting, and reuse a
relevant idle managed agent rather than creating a duplicate. Remote CLI access
does not expand the task boundary or authorize a permission prompt, job action,
credential action, publication, or destructive command.
Record host, session, pane/agent identifier, native agent session ID and working
directory. Inspect recent output as well as the status indicator before sending
a continuation prompt. Herdr detects agent state from the screen for every agent, so it can lag, and
a usage-limit wait can show as `done`. Lifecycle events pushed by a harness
plugin, where one exists, and the actual output provide stronger evidence.
Herdr never answers permission prompts; neither should a supervising agent.
Verify fresh state before relying on it for unattended coverage.

Let Herdr directly own managed agent panes. Avoid nesting managed agents inside
tmux or concurrently resuming the same native session elsewhere. Ordinary shells
can still use tmux. Keep remote inspection bounded and follow the existing SSH
connection policy rather than replacing a user's control master to fix a pane.

Herdr's integration for a harness can restore its native sessions after a
restart; check which native session it restored before prompting. Recovery
starts with inspection; see the
[recovery procedure](../../skills/session-coordination/references/recovery.md). Confirm the task, latest state and selected
session before restarting work. Restoration settings must not silently resume
old autonomous tasks. Notification does not mean delivery or acceptance; retain
the artifact and recipient identities in the handoff.

This first guide has not been exercised against a fresh Herdr installation.
No personal keybindings, phone relay or host inventory are required.
