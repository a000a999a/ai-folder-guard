"""Generate shell wrapper scripts that guard destructive commands for all AI tools."""
import os
import shutil
import stat
from pathlib import Path

BIN = Path.home() / ".local" / "bin"

# Find the real binary, skipping ~/.local/bin to avoid wrapping our own wrapper
def _real(cmd: str) -> str:
    local_bin = str(BIN)
    path_dirs = [d for d in os.environ.get("PATH", "").split(":") if d != local_bin]
    for d in path_dirs:
        p = Path(d) / cmd
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return f"/usr/bin/{cmd}"


_RM_GUARD = """\
#!/usr/bin/env bash
# ai-folder-guard: rm guard
REAL={real}

_dangerous() {{
    for a in "$@"; do
        case "$a" in -*r*|-*R*|--recursive) return 0;; esac
    done
    return 1
}}

if _dangerous "$@"; then
    printf '\\n\\033[33m⚠  AI FOLDER GUARD: recursive delete\\033[0m\\n' >/dev/tty
    printf '   rm %s\\n   Approve? [y/N] ' "$*" >/dev/tty
    read -r ans </dev/tty
    case "$ans" in [yY]*) ;; *) printf 'Blocked.\\n' >/dev/tty; exit 1;; esac
fi
exec "$REAL" "$@"
"""

_GIT_GUARD = """\
#!/usr/bin/env bash
# ai-folder-guard: git guard
REAL={real}

_dangerous() {{
    local sub="$1"; shift
    case "$sub" in
        reset) for a in "$@"; do [[ "$a" == "--hard" ]] && return 0; done;;
        push)  for a in "$@"; do [[ "$a" == "--force" || "$a" == "-f" || "$a" == "--force-with-lease" ]] && return 0; done;;
        clean) for a in "$@"; do [[ "$a" == -*f* ]] && return 0; done;;
        branch) for a in "$@"; do [[ "$a" == "-D" ]] && return 0; done;;
    esac
    return 1
}}

if _dangerous "$@"; then
    printf '\\n\\033[33m⚠  AI FOLDER GUARD: destructive git operation\\033[0m\\n' >/dev/tty
    printf '   git %s\\n   Approve? [y/N] ' "$*" >/dev/tty
    read -r ans </dev/tty
    case "$ans" in [yY]*) ;; *) printf 'Blocked.\\n' >/dev/tty; exit 1;; esac
fi
exec "$REAL" "$@"
"""

_DOCKER_GUARD = """\
#!/usr/bin/env bash
# ai-folder-guard: docker guard
REAL={real}

_dangerous() {{
    case "$1" in rm|rmi) return 0;; esac
    case "$1 $2" in "system prune"|"volume rm"|"container prune"|"image prune") return 0;; esac
    return 1
}}

if _dangerous "$@"; then
    printf '\\n\\033[33m⚠  AI FOLDER GUARD: destructive docker operation\\033[0m\\n' >/dev/tty
    printf '   docker %s\\n   Approve? [y/N] ' "$*" >/dev/tty
    read -r ans </dev/tty
    case "$ans" in [yY]*) ;; *) printf 'Blocked.\\n' >/dev/tty; exit 1;; esac
fi
exec "$REAL" "$@"
"""

_TEMPLATES = {"rm": _RM_GUARD, "git": _GIT_GUARD, "docker": _DOCKER_GUARD}


def _wrapper_path(cmd: str) -> Path:
    return BIN / cmd


def _is_guard(path: Path, cmd: str) -> bool:
    if not path.exists():
        return False
    try:
        return "ai-folder-guard" in path.read_text()
    except Exception:
        return False


def install(cmds: list = None) -> list:
    cmds = cmds or list(_TEMPLATES.keys())
    BIN.mkdir(parents=True, exist_ok=True)
    installed = []
    for cmd in cmds:
        if cmd not in _TEMPLATES:
            continue
        real = _real(cmd)
        wrapper = _wrapper_path(cmd)
        if wrapper.exists() and not _is_guard(wrapper, cmd):
            print(f"  Skipping {cmd}: {wrapper} exists and is not ours.")
            continue
        wrapper.write_text(_TEMPLATES[cmd].format(real=real))
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(cmd)
    return installed


def uninstall(cmds: list = None) -> list:
    cmds = cmds or list(_TEMPLATES.keys())
    removed = []
    for cmd in cmds:
        wrapper = _wrapper_path(cmd)
        if _is_guard(wrapper, cmd):
            wrapper.unlink()
            removed.append(cmd)
    return removed


def status() -> dict:
    return {cmd: _is_guard(_wrapper_path(cmd), cmd) for cmd in _TEMPLATES}
