#!/usr/bin/env python3
"""My Agents registry: keeps track of every agent built with the Agent Builder.

Default location (Claude Code): ~/.claude/agent-builder/my-agents.json
On claude.ai, pass --registry pointing at the user's uploaded my-agents.json.

Usage:
  agent_registry.py [--registry PATH] list [--all] [--tag TAG] [--usable-here] [--here DIR] [--json]
  agent_registry.py [--registry PATH] show <id>
  agent_registry.py [--registry PATH] check <id>
  agent_registry.py [--registry PATH] how <id>
  agent_registry.py [--registry PATH] set-usage <id> --start "first message" [--example "..." ...] [--guide PATH]
  agent_registry.py [--registry PATH] upsert <entry.json>
  agent_registry.py [--registry PATH] set-tests <id> --passed N --total N [--method M]
  agent_registry.py [--registry PATH] tag <id> [--add TAG ...] [--remove TAG ...]
  agent_registry.py [--registry PATH] note <id> "text"
  agent_registry.py [--registry PATH] archive <id>
  agent_registry.py [--registry PATH] restore <id>
  agent_registry.py [--registry PATH] remove <id>
  agent_registry.py [--registry PATH] dashboard <out.html> [--here DIR] [--open]

If a my-agents.html dashboard sits next to the registry, every change refreshes it.

The registry is per computer user, so it lists agents from every project.
Each agent has a scope: "personal" (works in every project) or "project"
(works only inside its "project" folder). File locations are always stored as
full paths so they mean the same thing from any project. "--here" (default:
the current folder) is used to mark agents that don't work in that project.

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
HISTORY_LIMIT = 10  # test runs kept per agent
INSTRUCTIONS_PREVIEW = 700  # characters of the agent's instructions shown in the dashboard
LOCAL_TYPES = {"subagent", "skill", "standalone-app"}
WIN_ABS = re.compile(r"^([A-Za-z]:[\\/]|\\\\)")
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


# ---------- paths and scope ----------

def is_abs(p) -> bool:
    p = str(p or "")
    return p.startswith(("/", "~")) or bool(WIN_ABS.match(p))


def resolve(p) -> Path:
    return Path(os.path.expanduser(str(p))).resolve(strict=False)


def scope_of(a: dict) -> str:
    return a.get("scope") or ("project" if a.get("project") else "personal")


def project_name(a: dict) -> str:
    return Path(str(a.get("project", ""))).name or str(a.get("project", "?"))


def usable_in(a: dict, here: Path | None) -> bool:
    if scope_of(a) != "project":
        return True
    if here is None or not a.get("project"):
        return False
    proj = resolve(a["project"])
    return here == proj or proj in here.parents


def local_paths(a: dict) -> list[tuple[str, str]]:
    """(what, path) for everything of this agent that lives on this computer."""
    out = []
    for d in a.get("destinations", []) or []:
        if d.get("type") in LOCAL_TYPES and d.get("location"):
            out.append((DEST_LABELS[d["type"]], d["location"]))
    brief = a.get("brief_path")
    if brief and brief != "kept by user":
        out.append(("Agent folder (brief, tests)", str(Path(str(brief)).parent)))
    return out


def unclear(a: dict) -> bool:
    return any(not is_abs(p) for _, p in local_paths(a)) or (scope_of(a) == "project" and not is_abs(a.get("project")))


def missing(a: dict) -> list[str]:
    return [p for _, p in local_paths(a) if is_abs(p) and not resolve(p).exists()]


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
    scope = e.get("scope", "project" if e.get("project") else "personal")
    if scope not in ("personal", "project"):
        problems.append("'scope' must be 'personal' or 'project'")
    if e.get("project") and not is_abs(e["project"]):
        problems.append("'project' must be the project folder's full path (e.g. /Users/sam/acme-site)")
    if scope == "project" and not e.get("project"):
        problems.append("a project agent needs 'project': the full path of the project folder")
    for d in e.get("destinations", []) or []:
        if isinstance(d, dict) and d.get("type") in LOCAL_TYPES:
            loc = d.get("location", "")
            if not is_abs(loc):
                problems.append(f"{d['type']} location must be a full path (starting with / or ~), got '{loc}'")
            elif scope == "project" and e.get("project") and d["type"] in ("subagent", "skill"):
                proj, where = resolve(e["project"]), resolve(loc)
                if proj not in where.parents:
                    problems.append(f"this project agent's {d['type']} file should be inside {e['project']}, got '{loc}'")
    brief = e.get("brief_path")
    if brief and brief != "kept by user" and not is_abs(brief):
        problems.append("'brief_path' must be a full path, or 'kept by user'")
    if e.get("usage") is not None:
        problems += validate_usage(e["usage"])
    return problems


def validate_usage(usage) -> list[str]:
    problems = []
    if not isinstance(usage, dict):
        problems.append("'usage' must be an object like {\"start\": \"...\", \"examples\": [...]}")
    else:
        if not str(usage.get("start", "")).strip():
            problems.append("'usage.start' is required: the exact first message to type to use the agent")
        if "examples" in usage and not isinstance(usage["examples"], list):
            problems.append("'usage.examples' must be a list")
        guide = usage.get("guide_path")
        if guide and not is_abs(guide):
            problems.append("'usage.guide_path' must be a full path to HOW-TO-USE.md")
    return problems


# ---------- display helpers ----------

def test_badge(a: dict) -> str:
    t = a.get("tests") or {}
    if not t.get("total"):
        return "· not tested"
    icon = "✅" if t.get("passed") == t.get("total") else "❌"
    return f"{icon} {t.get('passed', 0)}/{t['total']}"


def dest_short(a: dict) -> str:
    short = {"claude-ai-project": "claude.ai Project", "subagent": "subagent", "skill": "skill", "standalone-app": "app"}
    labels = [short.get(d.get("type"), "?") for d in a.get("destinations", []) or []]
    return ", ".join(labels) or "—"


def cut(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------- commands ----------

def display_scope(a: dict) -> str:
    """Like scope_of, but 'unknown' for old entries saved without a scope and with unclear paths."""
    if not a.get("scope") and not a.get("project") and unclear(a):
        return "unknown"
    return scope_of(a)


def scope_label(a: dict) -> str:
    sc = display_scope(a)
    return f"project: {project_name(a)}" if sc == "project" else ("unknown" if sc == "unknown" else "everywhere")


def cmd_list(data, args):
    here = resolve(args.here)
    agents = data["agents"]
    active = [a for a in agents if a.get("status", "active") == "active"]
    archived = [a for a in agents if a.get("status") == "archived"]
    shown = active + (archived if args.all else [])
    if args.tag:
        shown = [a for a in shown if args.tag.lower() in [t.lower() for t in a.get("tags", [])]]
    if args.usable_here:
        shown = [a for a in shown if usable_in(a, here)]
    if args.json:
        print(json.dumps(shown, ensure_ascii=False, indent=2))
        return
    if not agents:
        print("🗂️ My Agents: none yet. Build one with /agent-builder:create-agent.")
        return
    not_here = sum(1 for a in active if not usable_in(a, here))
    extra = f" · {not_here} only work in other projects" if not_here else ""
    print(f"🗂️ My Agents: {len(active)} active · {len(archived)} archived{extra}   (here: {here})")
    if not shown:
        print("   (no agents match)")
    for a in shown:
        tags = " ".join(f"#{t}" for t in a.get("tags", []))
        flags = []
        if a.get("status") == "archived":
            flags.append("[archived]")
        if not usable_in(a, here):
            flags.append(f"⛔ only works in {project_name(a)}" if a.get("project") else "⛔ project unknown")
        if a.get("status", "active") == "active" and not has_usage(a):
            flags.append("· no start message (say: add how-to-use for " + a["id"] + ")")
        if unclear(a):
            flags.append("⚠ location unclear, update this agent to fix")
        elif missing(a):
            flags.append("⚠ file missing")
        print(f"{a.get('emoji', '🤖')} {cut(a['name'], 22):<22}  {cut(a['tagline'], 40):<40}  "
              f"{cut(dest_short(a), 18):<18}  {cut(scope_label(a), 22):<22}  {test_badge(a):<10} {tags}  {'  '.join(flags)}".rstrip())
    if archived and not args.all:
        print(f"   ({len(archived)} archived agent(s) hidden; add --all to show)")


def cmd_show(data, args):
    print(json.dumps(find(data, args.id), ensure_ascii=False, indent=2))


def guide_path(a: dict) -> str | None:
    """Full path of the agent's HOW-TO-USE.md (given, or next to agent-brief.md)."""
    g = (a.get("usage") or {}).get("guide_path")
    if g and is_abs(g):
        return g
    brief = a.get("brief_path")
    if brief and brief != "kept by user" and is_abs(brief):
        return str(Path(str(brief)).parent / "HOW-TO-USE.md")
    return None


def start_phrase(a: dict) -> str:
    """The first thing to type to use the agent; a sensible default for older entries."""
    start = str((a.get("usage") or {}).get("start", "")).strip()
    if start:
        return start
    types = [d.get("type") for d in a.get("destinations", []) or []]
    if "skill" in types:
        return f"/{a['id']}"
    if "subagent" in types:
        return f"Use the {a['id']} agent to <what you need>"
    return "<your first request>"


def how_steps(a: dict) -> list[tuple[str, list[str]]]:
    """(destination label, steps) in plain words. Mirrors howSteps() in the dashboard."""
    start, out = start_phrase(a), []
    where = f"Open Claude Code in your {project_name(a)} project (it only works there)." if scope_of(a) == "project" \
        else "Open Claude Code in any project."
    for d in a.get("destinations", []) or []:
        t, loc = d.get("type"), str(d.get("location", ""))
        if t == "subagent":
            out.append((DEST_LABELS[t], [where, f"Type: {start}", f"Or type @ and pick {a['id']} from the list.",
                                         f"To make it the main agent for a whole session, start Claude Code with: claude --agent {a['id']}"]))
        elif t == "skill":
            ask = f"Type /{a['id']}" + ("" if start == f"/{a['id']}" else f", or just ask: {start}")
            out.append((DEST_LABELS[t], [where, ask,
                                         "On claude.ai (if you uploaded the skill): turn it on under Settings → Capabilities → Skills, then ask in any chat."]))
        elif t == "claude-ai-project":
            name = loc.split(":", 1)[1].strip() if ":" in loc else a.get("name", a["id"])
            out.append((DEST_LABELS[t], ["Go to claude.ai and click Projects.", f"Open the project \"{name}\".",
                                         f"Start a new chat inside the project and type: {start}"]))
        elif t == "standalone-app":
            folder = str(Path(loc)) if loc else "the agent's folder"
            out.append((DEST_LABELS[t], [f"Open a terminal in {folder}",
                                         "Turn on its Python environment: source .venv/bin/activate  (Windows: .venv\\Scripts\\Activate.ps1)",
                                         "Start it: python agent.py", f"Type: {start}   (type quit to stop)"]))
    return out


def cmd_how(data, args):
    """How to start using this agent, in plain steps."""
    a = find(data, args.id)
    print(f"▶️ How to use {a.get('emoji', '🤖')} {a['name']} ({a['id']})")
    if a.get("status") == "archived":
        print(f"   (archived: say \"restore {a['id']}\" first if its files were moved aside)")
    for label, steps in how_steps(a) or [("", ["No place to use it is recorded yet. Say \"update " + a["id"] + "\" to set it up."])]:
        if label:
            print(f"\n{label}:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
    examples = (a.get("usage") or {}).get("examples") or []
    if examples:
        print("\nTry these first:")
        for ex in examples:
            print(f"  - {ex}")
    g = guide_path(a)
    if g and resolve(g).exists():
        print(f"\nFull guide (setup details too): {resolve(g)}")


def has_usage(a: dict) -> bool:
    return bool(str((a.get("usage") or {}).get("start", "")).strip())


def cmd_set_usage(data, args):
    """Save how to start using an agent, without touching anything else (no new version)."""
    a = find(data, args.id)
    usage = dict(a.get("usage") or {})
    usage["start"] = args.start.strip()
    if args.example is not None:
        usage["examples"] = [x.strip() for x in args.example if x.strip()]
    if args.guide:
        usage["guide_path"] = args.guide
    problems = validate_usage(usage)
    if problems:
        fail("Usage problems:\n  - " + "\n  - ".join(problems))
    a["usage"] = usage
    print(f"{a['name']}: saved how to start using it. Run 'how {a['id']}' to see the steps.")
    return True


def cmd_check(data, args):
    """Where this agent's files are, as full paths, and whether they still exist."""
    a = find(data, args.id)
    print(f"{a.get('emoji', '🤖')} {a['name']} ({a['id']})")
    if scope_of(a) == "project":
        print(f"Works in: project {a.get('project', '(unknown)')} only")
    else:
        print("Works in: every project (personal)")
    for d in a.get("destinations", []) or []:
        if d.get("type") not in LOCAL_TYPES:
            print(f"  ☁️  {d.get('location') or DEST_LABELS.get(d.get('type'), d.get('type'))} (not on this computer; remove it by hand)")
    paths = local_paths(a)
    if not paths:
        print("  (no files on this computer)")
    for what, p in paths:
        if not is_abs(p):
            print(f"  ⚠️  {what}: '{p}' is not a full path. Can't tell which project it's in, so don't delete or move it automatically.")
        else:
            full = resolve(p)
            print(f"  {'✅' if full.exists() else '❌ missing'}  {what}: {full}")


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
        if "scope" in entry or "project" in entry:  # otherwise keep the existing scope and project
            merged["scope"] = entry.get("scope") or ("project" if entry.get("project") else "personal")
            if merged["scope"] == "personal":
                merged.pop("project", None)
        else:
            merged["scope"] = scope_of(existing)
        merged["version"] = int(existing.get("version", 1)) + 1
        merged["updated"] = stamp
        data["agents"][data["agents"].index(existing)] = merged
        print(f"Updated {merged['name']} (version {merged['version']}).")
    else:
        new = {"status": "active", "tags": [], "notes": "", "abilities": [], "destinations": [], "tests": None, **entry}
        new["scope"] = scope_of(new)
        new.update(created=stamp, updated=stamp, version=1)
        data["agents"].append(new)
        print(f"Added {new['name']} to My Agents ({len(data['agents'])} total).")
    return True


def cmd_set_tests(data, args):
    a = find(data, args.id)
    if args.passed < 0 or args.total < 0 or args.passed > args.total:
        fail("--passed must be between 0 and --total")
    a["tests"] = {"passed": args.passed, "total": args.total, "last_run": now(), "method": args.method}
    if args.report:
        a["tests"]["report"] = args.report
    a["test_history"] = ([dict(a["tests"])] + list(a.get("test_history") or []))[:HISTORY_LIMIT]
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
    paths = local_paths(a)
    if paths:
        print("Files that belonged to it:\n  " + "\n  ".join(
            f"{what}: {resolve(p) if is_abs(p) else p}" for what, p in paths))
    return True


def instructions_preview(a: dict) -> str:
    """First part of the '## Instructions' section of agent-brief.md, if readable."""
    brief = a.get("brief_path")
    if not brief or not is_abs(brief):
        return ""
    try:
        text = resolve(brief).read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^## Instructions\s*\n(.*)", text, re.S | re.M)
    body = (m.group(1) if m else "").strip()
    return body if len(body) <= INSTRUCTIONS_PREVIEW else body[:INSTRUCTIONS_PREVIEW].rsplit(" ", 1)[0] + " …"


def file_uri(p) -> str | None:
    full = resolve(p)
    return full.as_uri() if full.exists() else None


def dashboard_extras(a: dict, here: Path) -> dict:
    """Display-only fields for the dashboard; never saved to the registry."""
    paths = []
    for what, p in local_paths(a):
        full = resolve(p) if is_abs(p) else None
        paths.append({"what": what, "path": str(full) if full else p, "exists": bool(full and full.exists())})
    agent_dir = Path(str(a["brief_path"])).parent if a.get("brief_path") and is_abs(a["brief_path"]) else None
    flow = file_uri(agent_dir / "agent-flow.html") if agent_dir else None
    report = None
    rep_path = (a.get("tests") or {}).get("report") or (str(agent_dir / "tests" / "test-report.html") if agent_dir else None)
    if rep_path and is_abs(rep_path):
        report = file_uri(rep_path)
    guide = guide_path(a)
    return {"scope": display_scope(a), "_usable_here": usable_in(a, here), "_unclear": unclear(a),
            "_missing": missing(a), "_paths": paths, "_instructions": instructions_preview(a),
            "_flow_url": flow, "_report_url": report, "_guide_url": file_uri(guide) if guide else None,
            "_project_name": project_name(a) if a.get("project") else None}


def write_dashboard(data: dict, out: Path, here: Path) -> Path:
    html = TEMPLATE.read_text(encoding="utf-8")
    a, b = html.index(START) + len(START), html.index(END)
    agents = []
    for ag in data["agents"]:  # add display-only hints; never saved to the registry
        agents.append({**ag, **dashboard_extras(ag, here)})
    payload = json.dumps({"generated": now(), "here": str(here), "here_name": here.name, "agents": agents},
                         ensure_ascii=False, indent=2)
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html[:a] + payload + html[b:], encoding="utf-8")
    return out.resolve()


def cmd_dashboard(data, args):
    out = write_dashboard(data, Path(args.output).expanduser(), resolve(args.here))
    print(f"Dashboard written to {out}")
    if args.open:
        webbrowser.open(out.as_uri())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--registry", default=str(DEFAULT_REGISTRY), help=f"registry file (default: {DEFAULT_REGISTRY})")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--all", action="store_true"); s.add_argument("--tag"); s.add_argument("--json", action="store_true")
    s.add_argument("--here", default=os.getcwd(), help="project folder to check against (default: current folder)")
    s.add_argument("--usable-here", action="store_true", help="only agents that work in --here")
    s = sub.add_parser("check"); s.add_argument("id")
    s = sub.add_parser("show"); s.add_argument("id")
    s = sub.add_parser("how"); s.add_argument("id")
    s = sub.add_parser("set-usage"); s.add_argument("id")
    s.add_argument("--start", required=True, help="the exact first message to type to use the agent")
    s.add_argument("--example", action="append", help="a request to try first (repeat for more; replaces the saved examples)")
    s.add_argument("--guide", help="full path of the agent's HOW-TO-USE.md, if it isn't next to agent-brief.md")
    s = sub.add_parser("upsert"); s.add_argument("entry")
    s = sub.add_parser("set-tests"); s.add_argument("id"); s.add_argument("--passed", type=int, required=True); s.add_argument("--total", type=int, required=True); s.add_argument("--method", default="live", choices=["live", "simulated", "manual"]); s.add_argument("--report", help="full path of the HTML test report")
    s = sub.add_parser("tag"); s.add_argument("id"); s.add_argument("--add", nargs="*"); s.add_argument("--remove", nargs="*")
    s = sub.add_parser("note"); s.add_argument("id"); s.add_argument("text")
    s = sub.add_parser("archive"); s.add_argument("id")
    s = sub.add_parser("restore"); s.add_argument("id")
    s = sub.add_parser("remove"); s.add_argument("id")
    s = sub.add_parser("dashboard"); s.add_argument("output"); s.add_argument("--open", action="store_true")
    s.add_argument("--here", default=os.getcwd(), help="project folder to check against (default: current folder)")
    args = p.parse_args()

    path = Path(args.registry).expanduser()
    data = load(path)
    handlers = {
        "list": cmd_list, "show": cmd_show, "check": cmd_check, "how": cmd_how, "set-usage": cmd_set_usage, "upsert": cmd_upsert, "set-tests": cmd_set_tests,
        "tag": cmd_tag, "note": cmd_note, "remove": cmd_remove, "dashboard": cmd_dashboard,
        "archive": lambda d, a: cmd_status(d, a, "archived"),
        "restore": lambda d, a: cmd_status(d, a, "active"),
    }
    if handlers[args.cmd](data, args):
        save(path, data)
        # Keep the saved dashboard page in step with the list, so a page the user
        # reloads always shows the latest changes.
        page = path.with_name("my-agents.html")
        if page.exists():
            try:
                write_dashboard(data, page, resolve(os.getcwd()))
                print(f"Dashboard refreshed: {page.resolve()} (reload it in your browser)")
            except (OSError, ValueError) as exc:
                print(f"(Couldn't refresh the dashboard at {page}: {exc})", file=sys.stderr)


if __name__ == "__main__":
    main()
