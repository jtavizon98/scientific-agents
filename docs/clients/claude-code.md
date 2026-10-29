# Claude Code

Documentation checked 2026-10-28:
https://code.claude.com/docs/en/skills

Claude Code discovers project skills under `.claude/skills/` and personal skills
under `~/.claude/skills/`. Skill folders may link to a maintained checkout.
Inspect existing same-named skills and account-synced skills before adding a
second copy. Keep dependent references with the skill; for workflow links outside
its directory, preserve the relative layout or update the links to your copy.

Invoke `/source-library` in a new local session and ask which file and workflow
it loaded. Check the actual selected revision and a linked resource, not just
the command's presence. If a newly created top-level skills directory is not
noticed, use `/reload-skills` where supported or restart the session.

These instructions concern local Claude Code. Cowork/cloud sessions do not
automatically read your local personal skill directories; follow their account
or project distribution mechanism. Computer/browser tools and sign-ins belong
to the session exposing them, not every terminal connected to the same project.

Status: instructions checked against vendor documentation; fresh-client
interactive discovery has not yet been exercised for this extraction.
