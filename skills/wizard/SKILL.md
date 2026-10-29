---
name: wizard
description: Use when a repeatable procedure requires human-only interactive steps, especially credential initialization, dashboard work, or reviewed recovery after a reboot or crash. Do not use for steps the agent can perform safely.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/mattpocock/skills/blob/3216582/skills/engineering/wizard/SKILL.md
  adapted-for: recovery and credential boundaries in scientific workflows
---

# Wizard

Create a small interactive Bash guide for a procedure that the human must
perform. The wizard is an interface to the owning documentation, not a new
source of policy and not permission to perform consequential actions.

## Decide whether a wizard is warranted

Use a wizard only when the procedure is repeatable and contains a real
human-only boundary, such as entering a passphrase, approving an external
action, navigating a third-party interface, or selecting work to recover after
an interruption. Use ordinary automation when the agent can safely perform and
verify every step.

Before drafting, read the repository instructions and the workflow that owns
the procedure. Identify the host, target, current state, authorization, recovery
path, and stop conditions. Show the proposed stages to the user before writing
the script.

## Protect credentials and authority

- Never request, capture, print, copy, or persist passwords, certificate
  passphrases, private keys, tokens, or credential-bearing configuration.
- Let the human run passphrase-bearing commands directly in their terminal.
- Status checks do not authorize initialization, renewal, submission,
  cancellation, pulling, mounting, or process changes.
- Put an explicit confirmation immediately before each consequential action.
- Keep recovery read-only until the human selects one session and authorizes
  the next action.

Where the project uses session records, preserve `BRIEF.md`, `STATE.md`, and
`RESULT.md` as the durable control record (see
[session-coordination](../session-coordination/SKILL.md)). A recovery wizard may
inspect and compare those files with Git, process, tmux, and remote-job state. It must not choose a
session, resume a prompt, update a checkout, or change a job on its own.

For a credential that needs a passphrase, such as a short-lived proxy or token,
check its status first, explain which host or node will own it, ask the user to
run the documented initialization command, and verify status afterward. Never
receive the passphrase. Keep credential readiness separate from job
submission.

## Author the script

- Keep the script shorter than the procedure it clarifies.
- Use one focused stage per human decision or action, in dependency order.
- Show progress and the exact expected result of each stage.
- Make read-only checks safe to rerun. Do not claim that consequential actions
  are idempotent unless their owning workflow proves it.
- Prefer existing helpers and documented commands over copied implementations.
- Do not add `.env` or GitHub-secret machinery unless the owning repository
  actually uses it.
- Do not source an environment-setup script under `set -u` unless it is known
  to tolerate it; isolate setup in a compatible shell when repository
  instructions require it.
- Save one-off wizards in an approved scratch location. Commit a wizard only
  when the user wants a durable procedure and the owning documentation links
  to it.

## Verify and hand off

Run `bash -n` and `shellcheck` when available. Trace every branch statically,
including cancellation and missing-tool paths. Do not run an interactive wizard
end to end without the user. State which stages remain human-controlled and
which actions still need authorization.
