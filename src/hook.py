#!/usr/bin/python3 -I
"""AI Folder Guard — Claude Code PreToolUse hook.

Reads ~/.config/ai-folder-guard/config.json and blocks or prompts before
any tool touches a protected path. Self-contained: no external imports.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HOME = str(Path.home())
CONFIG_FILE = Path.home() / ".config" / "ai-folder-guard" / "config.json"
LOG_FILE    = Path.home() / ".config" / "ai-folder-guard" / "audit.log"

DEFAULT_CONFIG = {
    "mode": "blacklist",
    "blocked": [],
    "allowed": ["~/Projects", "~/.claude"],
    "exempt": [],
    "action": "ask",
}

_SPLIT = re.compile(r'[\s;|&()<>=`\'"]+')
_SYSTEM = ("/etc/", "/usr/", "/proc/", "/sys/", "/run/", "/dev/", "/tmp/claude-")

PATH_FIELDS = {
    "Read":        ("file_path",),
    "Edit":        ("file_path",),
    "Write":       ("file_path",),
    "NotebookEdit":("notebook_path",),
    "Glob":        ("path", "pattern"),
    "Grep":        ("path", "glob"),
}


def _expand(p: str) -> str:
    return p.replace("${HOME}", HOME).replace("$HOME", HOME).replace("~", HOME, 1)


def _under_home(p: str) -> bool:
    return p == HOME or p.startswith(HOME + "/")


def _load() -> dict:
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def _blocked(path: str, cfg: dict) -> bool:
    if not path:
        return False
    p = _expand(path)
    for e in cfg["exempt"]:
        ep = _expand(e)
        if p == ep or p.startswith(ep + "/"):
            return False
    if cfg["mode"] == "blacklist":
        for b in cfg["blocked"]:
            bp = _expand(b)
            if p == bp or p.startswith(bp + "/"):
                return True
        return False
    # whitelist mode: block anything under home not in allowed list
    if any(p.startswith(s) for s in _SYSTEM) or not _under_home(p):
        return False
    for a in cfg["allowed"]:
        ap = _expand(a)
        if p == ap or p.startswith(ap + "/"):
            return False
    return True


def _all_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _all_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _all_strings(v)


def _check(tool: str, inp: dict, cfg: dict):
    if tool in PATH_FIELDS:
        for field in PATH_FIELDS[tool]:
            p = inp.get(field) or ""
            if _blocked(p, cfg):
                return f"{tool} targets protected path '{p}'"
        return None
    if tool == "Bash":
        for tok in _SPLIT.split(inp.get("command", "")):
            if tok and _blocked(tok, cfg):
                return f"command references protected path '{tok}'"
        return None
    for s in _all_strings(inp):
        if _blocked(s, cfg):
            return f"{tool} input references protected path '{s}'"
    return None


def _log(tool: str, reason: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            ts = datetime.now().isoformat(timespec="seconds")
            f.write(f"{ts}\t{tool}\t{reason}\n")
    except Exception:
        pass


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    cfg = _load()
    tool = data.get("tool_name", "")
    inp  = data.get("tool_input") or {}
    reason = _check(tool, inp, cfg)
    if not reason:
        return
    _log(tool, reason)
    if cfg.get("action", "ask") == "deny":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"AI FOLDER GUARD: {reason}. Access denied by policy.",
        }}))
    else:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"AI FOLDER GUARD: {reason}. "
                "Files an AI reads are sent to the AI provider. "
                "Approve only if you explicitly want this path accessed."
            ),
        }}))


if __name__ == "__main__":
    main()
