"""AI Folder Guard — shared config management and path matching."""
import json
import os
from datetime import datetime
from pathlib import Path

HOME        = str(Path.home())
CONFIG_DIR  = Path.home() / ".config" / "ai-folder-guard"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE    = CONFIG_DIR / "audit.log"

DEFAULT_CONFIG = {
    "mode":    "blacklist",
    "blocked": [],
    "allowed": ["~/Projects", "~/.claude"],
    "exempt":  [],
    "action":  "ask",
}

_SYSTEM = ("/etc/", "/usr/", "/proc/", "/sys/", "/run/", "/dev/", "/tmp/claude-")


def load() -> dict:
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return dict(DEFAULT_CONFIG)


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def expand(p: str) -> str:
    return p.replace("${HOME}", HOME).replace("$HOME", HOME).replace("~", HOME, 1)


def _under_home(p: str) -> bool:
    return p == HOME or p.startswith(HOME + "/")


def is_blocked(path: str, cfg: dict) -> bool:
    if not path:
        return False
    p = expand(path)
    for e in cfg.get("exempt", []):
        ep = expand(e)
        if p == ep or p.startswith(ep + "/"):
            return False
    if cfg.get("mode", "blacklist") == "blacklist":
        for b in cfg.get("blocked", []):
            bp = expand(b)
            if p == bp or p.startswith(bp + "/"):
                return True
        return False
    if any(p.startswith(s) for s in _SYSTEM) or not _under_home(p):
        return False
    for a in cfg.get("allowed", []):
        ap = expand(a)
        if p == ap or p.startswith(ap + "/"):
            return False
    return True


def read_log(n: int = 50) -> list:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text().splitlines()
    result = []
    for line in reversed(lines[-n:]):
        parts = line.split("\t", 2)
        if len(parts) == 3:
            result.append({"ts": parts[0], "tool": parts[1], "path": parts[2]})
    return result
