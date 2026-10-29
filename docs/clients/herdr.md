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

Use the explicit named session: a default socket may refer to another server.
Record host, session, pane/agent identifier, native agent session ID and working
directory. Inspect recent output as well as the status indicator before sending
a continuation prompt. Screen-derived state can lag; lifecycle events and actual
outputs provide stronger evidence when available.

Let Herdr directly own managed agent panes. Avoid nesting managed agents inside
tmux or concurrently resuming the same native session elsewhere. Ordinary shells
can still use tmux. Keep remote inspection bounded and follow the existing SSH
connection policy rather than replacing a user's control master to fix a pane.

Recovery starts with inspection. Confirm the task, latest state and selected
session before restarting work. Restoration settings must not silently resume
old autonomous tasks. Notification does not mean delivery or acceptance; retain
the artifact and recipient identities in the handoff.

This first guide has not been exercised against a fresh Herdr installation.
No personal keybindings, phone relay or host inventory are required.
