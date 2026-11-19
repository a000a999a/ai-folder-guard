"""Install global git hooks that guard destructive operations for all AI tools."""
import os
import stat
import subprocess
from pathlib import Path

HOOKS_DIR = Path.home() / ".config" / "git" / "hooks"

_PRE_PUSH = """\
#!/usr/bin/env bash
# ai-folder-guard: pre-push hook
# Blocks force pushes to protected branches (main, master, develop).
remote="$1"
while read local_ref local_sha remote_ref remote_sha; do
    branch=$(basename "$remote_ref")
    case "$branch" in main|master|develop)
        # check if this is a non-fast-forward push
        if [ "$remote_sha" != "0000000000000000000000000000000000000000" ]; then
            if ! git merge-base --is-ancestor "$remote_sha" "$local_sha" 2>/dev/null; then
                printf '\\n\\033[33m⚠  AI FOLDER GUARD: force push to %s on %s\\033[0m\\n' "$branch" "$remote" >/dev/tty
                printf '   Approve? [y/N] ' >/dev/tty
                read -r ans </dev/tty
                case "$ans" in [yY]*) ;; *) printf 'Blocked.\\n' >/dev/tty; exit 1;; esac
            fi
        fi
    esac
done
exit 0
"""

_PRE_COMMIT = """\
#!/usr/bin/env bash
# ai-folder-guard: pre-commit hook
# Warns when a commit deletes more than 50 files at once.
deleted=$(git diff --cached --name-only --diff-filter=D | wc -l)
if [ "$deleted" -gt 50 ]; then
    printf '\\n\\033[33m⚠  AI FOLDER GUARD: commit deletes %d files\\033[0m\\n' "$deleted" >/dev/tty
    printf '   Approve? [y/N] ' >/dev/tty
    read -r ans </dev/tty
    case "$ans" in [yY]*) ;; *) printf 'Blocked.\\n' >/dev/tty; exit 1;; esac
fi
exit 0
"""

_HOOKS = {"pre-push": _PRE_PUSH, "pre-commit": _PRE_COMMIT}


def _is_ours(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return "ai-folder-guard" in path.read_text()
    except Exception:
        return False


def _global_hooks_path() -> str | None:
    result = subprocess.run(
        ["git", "config", "--global", "core.hooksPath"],
        capture_output=True, text=True
    )
    return result.stdout.strip() or None


def install() -> bool:
    """Returns True if hooks were installed, False if skipped."""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    existing = _global_hooks_path()
    if existing and existing != str(HOOKS_DIR):
        existing_dir = Path(existing)
        if existing_dir.exists():
            for name, body in _HOOKS.items():
                p = existing_dir / name
                if p.exists() and not _is_ours(p):
                    print(f"  Skipping {name}: existing hook in {existing_dir} is not ours.")
                    continue
                p.write_text(body)
                p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            return True
        print(f"  Warning: core.hooksPath set to {existing} (missing). Skipping.")
        return False
    for name, body in _HOOKS.items():
        p = HOOKS_DIR / name
        if p.exists() and not _is_ours(p):
            print(f"  Skipping {name}: existing hook not ours.")
            continue
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    subprocess.run(["git", "config", "--global", "core.hooksPath", str(HOOKS_DIR)], check=True)
    return True


def uninstall() -> None:
    for name in _HOOKS:
        p = HOOKS_DIR / name
        if _is_ours(p):
            p.unlink()
    if _global_hooks_path() == str(HOOKS_DIR):
        subprocess.run(["git", "config", "--global", "--unset", "core.hooksPath"])


def status() -> dict:
    return {name: _is_ours(HOOKS_DIR / name) for name in _HOOKS}
