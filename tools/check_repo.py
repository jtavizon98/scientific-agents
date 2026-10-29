#!/usr/bin/env python3
"""Check skill frontmatter and relative Markdown links. Standard library only."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_upstream import parse_pin  # noqa: E402

SKIP_DIRS = {".git", "node_modules", "build", "dist", "__pycache__", ".pytest_cache", ".venv"}
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*(```|~~~)")


def frontmatter(text):
    """Top-level `key: value` pairs of the leading YAML block, or None."""
    match = re.match(r"---\r?\n(.*?)\r?\n---\s*(\r?\n|$)", text, re.S)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        pair = re.match(r"([A-Za-z][\w-]*):\s*(.*)$", line)
        if pair:
            fields[pair.group(1)] = pair.group(2).strip().strip("\"'")
    return fields


def check_skills(root):
    problems = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        folder = skill.parent
        rel = skill.relative_to(root)
        fields = frontmatter(skill.read_text(encoding="utf-8"))
        if fields is None:
            problems.append(f"{rel}: missing YAML frontmatter")
            continue
        if fields.get("name") != folder.name:
            problems.append(f"{rel}: name {fields.get('name')!r} does not match folder {folder.name!r}")
        if not fields.get("description") or fields["description"] in {">", "|", ">-", "|-"}:
            problems.append(f"{rel}: empty description")
        if "LICENSE.txt" in fields.get("license", "") and not (folder / "LICENSE.txt").is_file():
            problems.append(f"{rel}: license names LICENSE.txt but the file is missing")
        if "LICENSE.txt" in fields.get("license", "") and not parse_pin(skill.read_text(encoding="utf-8")):
            problems.append(f"{rel}: adapted skill needs a metadata.source GitHub blob URL ending in /SKILL.md")
    return problems


def markdown_files(root):
    for path in sorted(root.rglob("*.md")):
        if not SKIP_DIRS.intersection(path.relative_to(root).parts):
            yield path


def check_links(root):
    problems = []
    for path in markdown_files(root):
        in_fence = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if FENCE.match(line):
                in_fence = not in_fence
            if in_fence:
                continue
            for target in LINK.findall(line):
                if re.match(r"([a-z][a-z0-9+.-]*:|#)", target, re.I):
                    continue
                file_part = target.split("#", 1)[0].split("?", 1)[0]
                if file_part and not (path.parent / file_part).exists():
                    problems.append(f"{path.relative_to(root)}: broken link {target}")
    return problems


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0] if args else Path(__file__).parents[1]).resolve()
    problems = check_skills(root) + check_links(root)
    print("\n".join(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
