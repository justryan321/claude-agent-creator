#!/usr/bin/env python3
"""My Agents registry: keeps track of every agent built with the Agent Builder.

Default location (Claude Code): ~/.claude/agent-builder/my-agents.json
On claude.ai, pass --registry pointing at the user's uploaded my-agents.json.

Usage:
  agent_registry.py [--registry PATH] list [--all] [--tag TAG] [--json]
  agent_registry.py [--registry PATH] show <id>
  agent_registry.py [--registry PATH] upsert <entry.json>
  agent_registry.py [--registry PATH] set-tests <id> --passed N --total N [--method M]
  agent_registry.py [--registry PATH] tag <id> [--add TAG ...] [--remove TAG ...]
  agent_registry.py [--registry PATH] note <id> "text"
  agent_registry.py [--registry PATH] archive <id>
  agent_registry.py [--registry PATH] restore <id>
  agent_registry.py [--registry PATH] remove <id>
  agent_registry.py [--registry PATH] dashboard <out.html> [--open]

Standard library only. Every write keeps a .bak copy of the previous file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

DEFAULT_REGISTRY = Path.home() / ".claude" / "agent-builder" / "my-agents.json"
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "dashboard-template.html"
START, END = "/*AGENTS_DATA_START*/", "/*AGENTS_DATA_END*/"
SCHEMA = 1
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DEST_LABELS = {
    "claude-ai-project": "Claude.ai Project",
    "subagent": "Claude Code subagent",
    "skill": "Claude skill",
    "standalone-app": "Standalone app",
}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def fail(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


# ---------- storage ----------

def load(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "agents": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        bak = path.with_suffix(path.suffix + ".bak")
        hint = f" A backup of the previous version is at {bak}." if bak.exists() else ""
        fail(f"The registry file {path} is damaged ({exc.msg}, line {exc.lineno}).{hint}")
    if not isinstance(data, dict) or not isinstance(data.get("agents"), list):
        fail(f"{path} doesn't look like a My Agents registry (expected {{\"schema\": 1, \"agents\": [...]}}).")
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    data["schema"] = SCHEMA
    data["agents"].sort(key=lambda a: a.get("updated", ""), reverse=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".my-agents-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def find(data: dict, agent_id: str) -> dict:
    for a in data["agents"]:
        if a.get("id") == agent_id:
            return a
    known = ", ".join(a.get("id", "?") for a in data["agents"]) or "none yet"
    fail(f"No agent with id '{agent_id}'. Known agents: {known}.")


# ---------- validation ----------

def validate_entry(e: dict) -> list[str]:
    problems = []
    if not ID_RE.match(str(e.get("id", ""))):
        problems.append("'id' must be lowercase letters, digits and hyphens (e.g. page-summarizer)")
    for field in ("name", "tagline"):
        if not str(e.get(field, "")).strip():
            problems.append(f"'{field}' is required")
    for field in ("abilities", "tags", "destinations"):
        if field in e and not isinstance(e[field], list):
            problems.append(f"'{field}' must be a list")
    for d in e.get("destinations", []) or []:
        if not isinstance(d, dict) or d.get("type") not in DEST_LABELS:
            problems.append(f"each destination needs a 'type' of {sorted(DEST_LABELS)}")
            break
    if e.get("status", "active") not in ("active", "archived"):
        problems.append("'status' must be 'active' or 'archived'")
    return problems


# ---------- display helpers ----------

def test_badge(a: dict) -> str:
    t = a.get("tests") or {}
    if not t.get("total"):
        return "· not tested"
    icon = "✅" if t.get("passed") == t.get("total") else "❌"
    return f"{icon} {t.get('passed', 0)}/{t['total']}"


def dest_short(a: dict) -> str:
    labels = [DEST_LABELS.get(d.get("type"), "?").replace("Claude Code ", "").replace("Claude.ai ", "")
              for d in a.get("destinations", []) or []]
    return ", ".join(labels) or "—"


def cut(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------- commands ----------

def cmd_list(data, args):
    agents = data["agents"]
    active = [a for a in agents if a.get("status", "active") == "active"]
    archived = [a for a in agents if a.get("status") == "archived"]
    shown = active + (archived if args.all else [])
    if args.tag:
        shown = [a for a in shown if args.tag.lower() in [t.lower() for t in a.get("tags", [])]]
    if args.json:
        print(json.dumps(shown, ensure_ascii=False, indent=2))
        return
    if not agents:
        print("🗂️ My Agents: none yet. Build one with /agent-builder:create-agent.")
        return
    print(f"🗂️ My Agents: {len(active)} active · {len(archived)} archived")
    if not shown:
        print("   (no agents match)")
    for a in shown:
        tags = " ".join(f"#{t}" for t in a.get("tags", []))
        arch = "  [archived]" if a.get("status") == "archived" else ""
        print(f"{a.get('emoji', '🤖')} {cut(a['name'], 22):<22}  {cut(a['tagline'], 46):<46}  "
              f"{cut(dest_short(a), 22):<22}  {test_badge(a):<10} {tags}{arch}".rstrip())
    if archived and not args.all:
        print(f"   ({len(archived)} archived agent(s) hidden; add --all to show)")


def cmd_show(data, args):
    print(json.dumps(find(data, args.id), ensure_ascii=False, indent=2))


def cmd_upsert(data, args):
    try:
        entry = json.loads(Path(args.entry).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Couldn't read the entry file: {exc}")
    problems = validate_entry(entry)
    if problems:
        fail("Entry problems:\n  - " + "\n  - ".join(problems))
    existing = next((a for a in data["agents"] if a.get("id") == entry["id"]), None)
    stamp = now()
    if existing:
        tags = list(dict.fromkeys((existing.get("tags") or []) + (entry.get("tags") or [])))
        merged = {**existing, **{k: v for k, v in entry.items() if k not in ("created", "version")}}
        merged["tags"] = tags
        if not str(entry.get("notes", "")).strip():
            merged["notes"] = existing.get("notes", "")
        if "tests" not in entry:
            merged["tests"] = existing.get("tests")
        merged["version"] = int(existing.get("version", 1)) + 1
        merged["updated"] = stamp
        data["agents"][data["agents"].index(existing)] = merged
        print(f"Updated {merged['name']} (version {merged['version']}).")
    else:
        new = {"status": "active", "tags": [], "notes": "", "abilities": [], "destinations": [], "tests": None, **entry}
        new.update(created=stamp, updated=stamp, version=1)
        data["agents"].append(new)
        print(f"Added {new['name']} to My Agents ({len(data['agents'])} total).")
    return True


def cmd_set_tests(data, args):
    a = find(data, args.id)
    if args.passed < 0 or args.total < 0 or args.passed > args.total:
        fail("--passed must be between 0 and --total")
    a["tests"] = {"passed": args.passed, "total": args.total, "last_run": now(), "method": args.method}
    a["updated"] = now()
    print(f"{a['name']}: tests {test_badge(a)}")
    return True


def cmd_tag(data, args):
    a = find(data, args.id)
    tags = list(a.get("tags") or [])
    for t in args.add or []:
        t = t.strip().lstrip("#")
        if t and t.lower() not in [x.lower() for x in tags]:
            tags.append(t)
    remove = {t.strip().lstrip("#").lower() for t in args.remove or []}
    a["tags"] = [t for t in tags if t.lower() not in remove]
    a["updated"] = now()
    print(f"{a['name']}: " + (" ".join(f"#{t}" for t in a["tags"]) or "no tags"))
    return True


def cmd_note(data, args):
    a = find(data, args.id)
    a["notes"] = args.text.strip()
    a["updated"] = now()
    print(f"{a['name']}: note saved.")
    return True


def cmd_status(data, args, status):
    a = find(data, args.id)
    a["status"] = status
    a["updated"] = now()
    print(f"{a['name']} is now {status}.")
    return True


def cmd_remove(data, args):
    a = find(data, args.id)
    data["agents"].remove(a)
    print(f"Removed {a['name']} from My Agents. Its files were not touched.")
    files = [d.get("location") for d in a.get("destinations", []) or [] if d.get("location")]
    if a.get("brief_path"):
        files.append(a["brief_path"])
    if files:
        print("Files that belonged to it:\n  " + "\n  ".join(files))
    return True


def cmd_dashboard(data, args):
    html = TEMPLATE.read_text(encoding="utf-8")
    a, b = html.index(START) + len(START), html.index(END)
    payload = json.dumps({"generated": now(), "agents": data["agents"]}, ensure_ascii=False, indent=2)
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html[:a] + payload + html[b:], encoding="utf-8")
    print(f"Dashboard written to {out.resolve()}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--registry", default=str(DEFAULT_REGISTRY), help=f"registry file (default: {DEFAULT_REGISTRY})")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--all", action="store_true"); s.add_argument("--tag"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("show"); s.add_argument("id")
    s = sub.add_parser("upsert"); s.add_argument("entry")
    s = sub.add_parser("set-tests"); s.add_argument("id"); s.add_argument("--passed", type=int, required=True); s.add_argument("--total", type=int, required=True); s.add_argument("--method", default="live", choices=["live", "simulated", "manual"])
    s = sub.add_parser("tag"); s.add_argument("id"); s.add_argument("--add", nargs="*"); s.add_argument("--remove", nargs="*")
    s = sub.add_parser("note"); s.add_argument("id"); s.add_argument("text")
    s = sub.add_parser("archive"); s.add_argument("id")
    s = sub.add_parser("restore"); s.add_argument("id")
    s = sub.add_parser("remove"); s.add_argument("id")
    s = sub.add_parser("dashboard"); s.add_argument("output"); s.add_argument("--open", action="store_true")
    args = p.parse_args()

    path = Path(args.registry).expanduser()
    data = load(path)
    handlers = {
        "list": cmd_list, "show": cmd_show, "upsert": cmd_upsert, "set-tests": cmd_set_tests,
        "tag": cmd_tag, "note": cmd_note, "remove": cmd_remove, "dashboard": cmd_dashboard,
        "archive": lambda d, a: cmd_status(d, a, "archived"),
        "restore": lambda d, a: cmd_status(d, a, "active"),
    }
    if handlers[args.cmd](data, args):
        save(path, data)


if __name__ == "__main__":
    main()
