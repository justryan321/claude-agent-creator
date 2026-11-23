#!/usr/bin/env python3
"""Turn chat exports into readable text so the Agent Builder can reuse them.

Supports:
  * claude.ai data export (.zip, or the conversations.json inside it)
  * ChatGPT data export (.zip, or its conversations.json)
  * Claude Code sessions (a .jsonl file, or a ~/.claude/projects/<project>/ folder)

Usage:
  extract_conversations.py list   <source> [--limit N]
  extract_conversations.py search <source> <keyword> [--limit N]
  extract_conversations.py show   <source> <number-or-id> [--max-chars N]

Standard library only. Read-only: never modifies the source.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Conversation:
    id: str
    title: str
    updated: str  # ISO-ish timestamp string, may be ""
    messages: list[tuple[str, str]] = field(default_factory=list)  # (role, text)
    source: str = ""


# ---------- helpers ----------

def _ts(value) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    return str(value)[:16].replace("T", " ")


def _text_from_blocks(content) -> str:
    """Extract plain text from a string or a list of content blocks."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                btype = block.get("type")
                if btype in (None, "text") and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif btype == "tool_use":
                    parts.append(f"[used tool: {block.get('name', '?')}]")
                # thinking, images, tool results etc. are skipped
    elif isinstance(content, dict):
        return _text_from_blocks(content.get("parts") or content.get("text"))
    return "\n".join(p for p in parts if p and p.strip())


# ---------- format parsers ----------

def _parse_claude_export(data: list) -> list[Conversation]:
    convs = []
    for c in data:
        msgs = []
        for m in c.get("chat_messages", []) or []:
            role = "User" if m.get("sender") == "human" else "Claude"
            text = _text_from_blocks(m.get("content")) or m.get("text") or ""
            for att in m.get("attachments", []) or []:
                extracted = att.get("extracted_content")
                name = att.get("file_name", "attachment")
                if extracted:
                    text += f"\n\n[Attached file: {name}]\n{extracted}"
                else:
                    text += f"\n[Attached file: {name}]"
            if text.strip():
                msgs.append((role, text.strip()))
        convs.append(Conversation(
            id=str(c.get("uuid", "")),
            title=c.get("name") or "(untitled chat)",
            updated=_ts(c.get("updated_at") or c.get("created_at")),
            messages=msgs,
            source="claude.ai",
        ))
    return convs


def _parse_chatgpt_export(data: list) -> list[Conversation]:
    convs = []
    for c in data:
        mapping = c.get("mapping") or {}
        node_id = c.get("current_node")
        chain = []
        seen = set()
        while node_id and node_id in mapping and node_id not in seen:
            seen.add(node_id)
            chain.append(mapping[node_id])
            node_id = mapping[node_id].get("parent")
        msgs = []
        for node in reversed(chain):
            m = node.get("message") or {}
            role = (m.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue
            text = _text_from_blocks((m.get("content") or {}).get("parts"))
            if text.strip():
                msgs.append(("User" if role == "user" else "ChatGPT", text.strip()))
        convs.append(Conversation(
            id=str(c.get("conversation_id") or c.get("id") or ""),
            title=c.get("title") or "(untitled chat)",
            updated=_ts(c.get("update_time") or c.get("create_time")),
            messages=msgs,
            source="ChatGPT",
        ))
    return convs


def _parse_claude_code_session(path: Path) -> Conversation:
    msgs = []
    updated = ""
    title = ""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "summary" and entry.get("summary"):
                title = title or entry["summary"]
            if entry.get("type") not in ("user", "assistant") or entry.get("isMeta"):
                continue
            message = entry.get("message") or {}
            text = _text_from_blocks(message.get("content"))
            if not text.strip() or text.lstrip().startswith("<command-") or text.lstrip().startswith("<local-command"):
                continue
            role = "User" if entry["type"] == "user" else "Claude"
            msgs.append((role, text.strip()))
            updated = _ts(entry.get("timestamp")) or updated
    if not title:
        first_user = next((t for r, t in msgs if r == "User"), "(empty session)")
        title = first_user.splitlines()[0][:80]
    return Conversation(id=path.stem, title=title, updated=updated, messages=msgs, source="Claude Code")


def load(source: str) -> list[Conversation]:
    path = Path(source).expanduser()
    if not path.exists():
        sys.exit(f"Not found: {path}")

    if path.is_dir():
        sessions = sorted(path.glob("*.jsonl"))
        if sessions:
            convs = [_parse_claude_code_session(p) for p in sessions]
            return _sort([c for c in convs if c.messages])
        candidate = path / "conversations.json"
        if candidate.exists():
            return load(str(candidate))
        sys.exit(f"No conversations.json or .jsonl session files in {path}")

    if path.suffix == ".jsonl":
        return [_parse_claude_code_session(path)]

    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.endswith("conversations.json")]
            if not names:
                sys.exit("This zip has no conversations.json. Is it a Claude or ChatGPT data export?")
            data = json.loads(zf.read(sorted(names, key=len)[0]).decode("utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        sys.exit("Unrecognized file: expected a list of conversations.")
    sample = next((c for c in data if isinstance(c, dict)), {})
    if "chat_messages" in sample:
        return _sort(_parse_claude_export(data))
    if "mapping" in sample:
        return _sort(_parse_chatgpt_export(data))
    sys.exit("Unrecognized export format (expected a Claude or ChatGPT export).")


def _sort(convs: list[Conversation]) -> list[Conversation]:
    return sorted(convs, key=lambda c: c.updated, reverse=True)


# ---------- commands ----------

def _row(i: int, c: Conversation) -> str:
    return f"{i:>4}. {c.updated or '----------------'}  {c.title[:70]}  ({len(c.messages)} msgs)"


def cmd_list(convs, limit):
    print(f"{len(convs)} conversation(s), newest first:\n")
    for i, c in enumerate(convs[:limit], 1):
        print(_row(i, c))
    if len(convs) > limit:
        print(f"\n... {len(convs) - limit} more. Use --limit or search by keyword.")


def cmd_search(convs, keyword, limit):
    kw = keyword.lower()
    hits = []
    for i, c in enumerate(convs, 1):
        in_title = kw in c.title.lower()
        count = sum(t.lower().count(kw) for _, t in c.messages)
        if in_title or count:
            hits.append((i, c, count, in_title))
    if not hits:
        print(f'No conversations mention "{keyword}".')
        return
    hits.sort(key=lambda h: (h[3], h[2]), reverse=True)
    print(f'{len(hits)} conversation(s) mention "{keyword}" (best matches first):\n')
    for i, c, count, _ in hits[:limit]:
        print(f"{_row(i, c)}  [{count} mention(s)]")


def cmd_show(convs, which, max_chars):
    conv = None
    if which.isdigit() and 1 <= int(which) <= len(convs):
        conv = convs[int(which) - 1]
    else:
        conv = next((c for c in convs if c.id == which or c.id.startswith(which)), None)
    if conv is None:
        sys.exit(f"No conversation '{which}'. Run 'list' to see the numbers.")

    out = [f"# {conv.title}", f"_Source: {conv.source} · {conv.updated} · {len(conv.messages)} messages_", ""]
    for role, text in conv.messages:
        out.append(f"**{role}:**\n{text}\n")
    result = "\n".join(out)
    if len(result) > max_chars:
        result = result[:max_chars] + f"\n\n[... truncated at {max_chars} characters; rerun with a larger --max-chars to see more]"
    print(result)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("list"); a.add_argument("source"); a.add_argument("--limit", type=int, default=40)
    b = sub.add_parser("search"); b.add_argument("source"); b.add_argument("keyword"); b.add_argument("--limit", type=int, default=20)
    c = sub.add_parser("show"); c.add_argument("source"); c.add_argument("which"); c.add_argument("--max-chars", type=int, default=60000)
    args = p.parse_args()

    convs = load(args.source)
    if args.cmd == "list":
        cmd_list(convs, args.limit)
    elif args.cmd == "search":
        cmd_search(convs, args.keyword, args.limit)
    else:
        cmd_show(convs, args.which, args.max_chars)


if __name__ == "__main__":
    main()
