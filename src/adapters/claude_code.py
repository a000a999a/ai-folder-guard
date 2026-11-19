"""Install / uninstall the ai-folder-guard hook in ~/.claude/settings.json."""
import json
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "settings.json"
HOOK_CMD  = str(Path.home() / ".config" / "ai-folder-guard" / "hook.py")
_ENTRY    = {"type": "command", "command": HOOK_CMD, "timeout": 10}
_MATCHER  = {"matcher": "*", "hooks": [_ENTRY]}


def _load() -> dict:
    return json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {}


def _save(s: dict) -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(s, indent=2))


def is_installed() -> bool:
    for entry in _load().get("hooks", {}).get("PreToolUse", []):
        if any(h.get("command") == HOOK_CMD for h in entry.get("hooks", [])):
            return True
    return False


def install() -> None:
    if is_installed():
        print("Hook already installed.")
        return
    src = Path(__file__).parent.parent / "hook.py"
    dst = Path(HOOK_CMD)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text())
    dst.chmod(0o755)
    s = _load()
    s.setdefault("hooks", {}).setdefault("PreToolUse", []).append(_MATCHER)
    _save(s)


def uninstall() -> None:
    s = _load()
    hooks = s.get("hooks", {}).get("PreToolUse", [])
    s["hooks"]["PreToolUse"] = [
        m for m in hooks
        if not any(h.get("command") == HOOK_CMD for h in m.get("hooks", []))
    ]
    _save(s)
