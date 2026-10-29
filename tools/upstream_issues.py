#!/usr/bin/env python3
"""Open or update GitHub issues from `check_upstream.py --json` output on stdin.

Needs the `gh` CLI with GH_TOKEN. Idempotent: the title is stable per upstream
directory and the body records the upstream tree SHA seen. An open issue is
edited; a closed one that recorded the same SHA counts as acknowledged;
otherwise a new issue is created. Nothing is closed or merged.
"""
import json
import subprocess
import sys


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def marker(state):
    return f"<!-- upstream-tree: {state} -->"


def upsert(title, body, state):
    """Edit the open issue; skip if the latest closed one saw this state; else create."""
    found = json.loads(gh("issue", "list", "--state", "all", "--search", f'"{title}" in:title',
                          "--limit", "100", "--json", "number,title,state,body,closedAt"))
    same = [i for i in found if i["title"] == title]
    body = f"{marker(state)}\n{body}"
    opened = [i for i in same if i["state"].upper() == "OPEN"]
    if opened:
        gh("issue", "edit", str(opened[0]["number"]), "--body", body)
        print(f"updated #{opened[0]['number']}: {title}")
        return
    closed = sorted((i for i in same if i.get("closedAt")), key=lambda i: i["closedAt"], reverse=True)
    if closed and marker(state) in (closed[0].get("body") or ""):
        print(f"acknowledged in #{closed[0]['number']}: {title}")
        return
    gh("issue", "create", "--title", title, "--body", body)  # a new issue, not a reopen
    print(f"created: {title}")


def issues(report):
    for pin in report["pins"]:
        if pin["status"] in ("changed", "missing"):
            where = f"{pin['owner']}/{pin['repo']}/{pin['parent']}/{pin['dir']}"
            yield (f"Upstream changed: {pin['skill']} ({where})",
                   f"Status: `{pin['status']}`\n\nPinned `{pin['commit']}`, upstream `{pin.get('branch')}`, "
                   f"directory `{pin['parent']}/{pin['dir']}`.\n\n"
                   + (f"Compare: {pin['compare']}\n" if "compare" in pin else f"{pin.get('detail', 'The directory no longer exists upstream.')}\n"),
                   pin.get("upstream_sha", "missing"))
    for new in report["new_folders"]:
        where = f"{new['owner']}/{new['repo']}/{new['parent']}"
        listing = "\n".join(f"- `{f}`" for f in new["folders"])
        yield (f"Upstream added skills: {where}",
               f"New folders on `{new['branch']}` absent at the pinned commits:\n\n{listing}\n",
               ",".join(new["folders"]))


def main():
    for title, body, state in issues(json.load(sys.stdin)):
        upsert(title, body, state)


if __name__ == "__main__":
    main()
