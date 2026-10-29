# Codex

Documentation checked 2026-10-28:
https://developers.openai.com/codex/build-skills

Codex CLI discovers project skills under `.agents/skills/` from the current
directory to the repository root, and personal skills under `~/.agents/skills/`.
Symlinked skill folders are supported. Inspect existing entries before adding
one: same-named skills can both appear rather than being merged.

For a self-contained skill, copy its whole directory into the selected discovery
location. For the connected workflow skills, either retain their linked
workflow/template files and adjust paths, or link to a maintained checkout.
Resolve relative resources against the actual skill directory, not your task's
working directory. Do not copy only SKILL.md and lose its references.

In a new session use `/skills` or explicitly mention `$source-library`. Ask it to
identify the skill file and read the linked workflow before doing a small task.
Confirm the file/revision matches your selected copy; a menu entry alone does
not verify its dependencies. If changes do not appear, restart Codex.

No model, permissions or account configuration is installed by these files.
GUI/browser availability depends on the actual client and connected tools; a
terminal session should hand off an unread protected source rather than claim
it accessed a desktop session's sign-in.

Status: instructions checked against vendor documentation; fresh-client
interactive discovery has not yet been exercised for this extraction.
