#!/usr/bin/env python3
"""Report upstream changes to adapted skills pinned in `metadata.source`.

Exit 0: nothing changed. 1: a pin changed, vanished (also a removed or moved
upstream path), or upstream added skill folders. 2: an API error occurred or no
pins were found. Standard library only; GITHUB_TOKEN is optional.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
SOURCE = re.compile(r"""^\s*source:\s*(["']?)https://github\.com/([^/\s]+)/([^/\s]+)/blob/([0-9a-f]{7,40})/([^\s"']+)/SKILL\.md\1\s*$""", re.M)
# A skill that folds in a second upstream skill pins it as `also-source`.
ALSO_SOURCE = re.compile(r"""^\s*also-source:\s*(["']?)https://github\.com/([^/\s]+)/([^/\s]+)/blob/([0-9a-f]{7,40})/([^\s"']+)/SKILL\.md\1\s*$""", re.M)


class ApiError(Exception):
    def __init__(self, status, message=""):
        super().__init__(f"HTTP {status} {message}".strip())
        self.status = status


def fetch(path):
    """GET a GitHub API path and return decoded JSON."""
    request = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "scientific-agents-drift-watch"})
    if os.environ.get("GITHUB_TOKEN"):
        request.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ApiError(error.code, error.reason) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise ApiError(0, str(error)) from error


def parse_pin(text):
    """(owner, repo, commit, directory) from the `metadata.source` blob URL, or None."""
    match = SOURCE.search(text.split("\n---", 1)[0])
    return match.groups()[1:] if match else None


def read_pins(root):
    pins = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        head = text.split("\n---", 1)[0]
        found = [parse_pin(text)] + [m.groups()[1:] for m in ALSO_SOURCE.finditer(head)]
        for owner, repo, commit, directory in filter(None, found):
            parent, _, name = directory.rpartition("/")
            pins.append({"skill": skill.parent.name, "owner": owner, "repo": repo,
                         "commit": commit, "parent": parent, "dir": name})
    return pins


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[1])
    args = parser.parse_args(argv)

    listings, branches = {}, {}

    def entries(owner, repo, parent, ref):
        key = (owner, repo, parent, ref)
        if key not in listings:
            try:
                data = fetch(f"/repos/{owner}/{repo}/contents/{parent}?ref={ref}")
            except ApiError as error:
                if error.status != 404:
                    raise
                listings[key] = None  # path absent at this ref; the repository itself resolved
                return None
            listings[key] = {e["name"]: e for e in data if e["type"] == "dir"}
        return listings[key]

    def branch(owner, repo):
        if (owner, repo) not in branches:
            branches[(owner, repo)] = fetch(f"/repos/{owner}/{repo}")["default_branch"]
        return branches[(owner, repo)]

    results, groups = [], {}
    pins = read_pins(args.root)
    if not pins:
        print("no upstream pins found in skills/*/SKILL.md", file=sys.stderr)
    for pin in pins:
        o, r, c, parent = pin["owner"], pin["repo"], pin["commit"], pin["parent"]
        result = dict(pin, status="error")
        try:
            result["branch"] = head = branch(o, r)
            old_list, new_list = entries(o, r, parent, c), entries(o, r, parent, head)
            old = (old_list or {}).get(pin["dir"])
            new = (new_list or {}).get(pin["dir"])
            if old is None:
                result["detail"] = "directory absent at the pinned commit"
            elif new is None:
                result["status"] = "missing"
                result["detail"] = (f"{parent} no longer exists on {head} (removed or moved)" if new_list is None
                                    else f"{parent}/{pin['dir']} no longer exists on {head} (removed or moved)")
            elif old["sha"] == new["sha"]:
                result["status"] = "unchanged"
            else:
                result["status"] = "changed"
            if new is not None:
                result["upstream_sha"] = new["sha"]
            if result["status"] == "changed":
                result["compare"] = f"https://github.com/{o}/{r}/compare/{c}...{head}"
            groups.setdefault((o, r, parent, head), []).append(c)
        except ApiError as error:
            result["detail"] = str(error)
        results.append(result)

    new_folders = []
    for (o, r, parent, head), commits in groups.items():
        try:
            known = set().union(*(entries(o, r, parent, c) or {} for c in commits))
            added = sorted(set(entries(o, r, parent, head) or {}) - known)
        except ApiError as error:
            results.append({"skill": f"{o}/{r}/{parent}", "status": "error", "detail": str(error)})
            continue
        if added:
            new_folders.append({"owner": o, "repo": r, "parent": parent, "branch": head, "folders": added})

    if args.json:
        print(json.dumps({"pins": results, "new_folders": new_folders}, indent=2))
    else:
        for item in results:
            label = item["skill"] if item.get("dir", item["skill"]) == item["skill"] else f"{item['skill']} ({item['dir']})"
            line = f"{label}: {item['status']}"
            print(line + (f" ({item['detail']})" if "detail" in item else "")
                  + (f" {item['compare']}" if "compare" in item else ""))
        for item in new_folders:
            print(f"new folders in {item['owner']}/{item['repo']}/{item['parent']}: " + ", ".join(item["folders"]))

    if not pins or any(i["status"] == "error" for i in results):
        return 2
    return 1 if new_folders or any(i["status"] != "unchanged" for i in results) else 0


if __name__ == "__main__":
    sys.exit(main())
