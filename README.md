# ai-folder-guard

Protect sensitive filesystem paths and guard destructive commands from AI coding tools — Claude Code, Cursor, Copilot, Aider, Continue, Cline and more.

## Protection overview

| Threat | Mechanism | Works for |
|---|---|---|
| AI reading sensitive files | `hook.py` PreToolUse hook | Claude Code |
| AI reading sensitive files | `.aiderignore`, `.cursorignore`, `.copilotignore` etc. | Aider, Cursor, Copilot, Continue, Cline |
| `rm -rf` on non-temp paths | `~/.local/bin/rm` shell wrapper | All tools |
| `git reset --hard` / `push --force` / `clean -f` | `~/.local/bin/git` shell wrapper | All tools |
| `docker rm` / `rmi` / `system prune` | `~/.local/bin/docker` shell wrapper | All tools |
| Force push to main/master/develop | `pre-push` global git hook | All tools |
| Commit deleting 50+ files at once | `pre-commit` global git hook | All tools |

## How it works

Three layers of protection:

1. **Folder guard** — blacklist or whitelist mode. Blacklist blocks named sensitive paths; whitelist blocks everything under home except explicitly allowed paths. Claude Code's PreToolUse hook intercepts every tool call before execution. Ignore-file adapters tell other AI tools which paths to skip.

2. **Shell guards** — thin wrapper scripts in `~/.local/bin/` that sit ahead of `rm`, `git` and `docker` in PATH. Any call with dangerous flags (recursive delete, force push, hard reset, container/image removal) triggers a prompt before the real command runs. Works for every tool that uses the shell.

3. **Git hooks** — global `pre-push` and `pre-commit` hooks via `core.hooksPath`. Catches force pushes to protected branches and large bulk deletions at the git level, regardless of which tool made the commit.

## Install

```bash
git clone https://github.com/a000a999a/ai-folder-guard
cd ai-folder-guard
bash install.sh
```

Requires Python 3.8+. Web UI requires Flask (`sudo pacman -S python-flask` on Arch/Manjaro, or `pip install flask`).

The installer automatically starts the web UI as a systemd user service on port 7799.

## Quick start

```bash
# Install all protections
folder-guard install --tool all

# Or pick what you need
folder-guard install --tool claude-code    # Claude Code hook
folder-guard install --tool shell-guards   # rm/git/docker wrappers
folder-guard install --tool git-hooks      # global git hooks

# Add a path to block
folder-guard add ~/.ssh
folder-guard add ~/Documents/Passwords

# Check status
folder-guard status
```

## Web UI

```
http://<machine-ip>:7799
```

The page shows the machine hostname prominently so you always know which machine you are editing. Add/remove blocked paths, switch modes, and view the audit log.

## Supported AI tools

| Tool | Adapter | How it works |
|------|---------|--------------|
| Claude Code | PreToolUse hook | Intercepts every tool call before execution |
| Cursor | `.cursorignore` | Excludes paths from Cursor's index |
| GitHub Copilot | `.copilotignore` | Excludes paths from Copilot context |
| Aider | `.aiderignore` | Excludes paths from Aider reads |
| Continue | `.continueignore` | Excludes paths from Continue context |
| Cline | `.clineignore` | Excludes paths from Cline context |

For ignore-file adapters, run in your project root:
```bash
folder-guard install --tool cursor --project /path/to/project
```

## CLI reference

```
folder-guard add <path>                        Add to blocked/allowed list
folder-guard remove <path>                     Remove from list
folder-guard exempt add|remove <path>          Manage exemptions
folder-guard list                              Show all configured paths
folder-guard mode blacklist|whitelist          Switch protection mode
folder-guard action ask|deny                   Set response action
folder-guard status                            Show full status
folder-guard install --tool <name>             Install adapter
folder-guard uninstall --tool <name>           Remove adapter
folder-guard serve [--port 7799]               Start web UI
folder-guard log [--n 20]                      Show audit log
```

Available tools: `claude-code`, `shell-guards`, `git-hooks`, `cursor`, `copilot`, `aider`, `continue`, `cline`, `all`

## Config

Config lives at `~/.config/ai-folder-guard/config.json`. See `config.example.json` for the full schema.

## License

MIT
