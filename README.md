# ai-folder-guard

Protect sensitive filesystem paths from AI coding tools — Claude Code, Cursor, Copilot, Aider and more.

## How it works

A lightweight Python hook sits in front of every tool call. When an AI tries to read, edit, or run a command touching a protected path it either prompts you first (ask mode) or blocks the access outright (deny mode).

Two protection modes:
- **Blacklist** — explicitly block named paths (e.g. `~/.ssh`, `~/Documents/TaxData`)
- **Whitelist** — allow only named paths under home; block everything else

## Install

```bash
git clone https://github.com/a000a999a/ai-folder-guard
cd ai-folder-guard
bash install.sh
```

Requires Python 3.8+. Web UI requires Flask (`pip install flask`).

## Quick start

```bash
folder-guard status
folder-guard add ~/.ssh
folder-guard add ~/Documents/Passwords
folder-guard install --tool claude-code
```

Open the web UI:
```bash
folder-guard serve     # http://127.0.0.1:7799
```

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
folder-guard add <path>                    Add to blocked/allowed list
folder-guard remove <path>                 Remove from list
folder-guard exempt add|remove <path>      Manage exemptions
folder-guard list                          Show all configured paths
folder-guard mode blacklist|whitelist      Switch protection mode
folder-guard action ask|deny              Set response action
folder-guard status                        Show current status
folder-guard install --tool <name>         Install adapter
folder-guard uninstall --tool <name>       Remove adapter
folder-guard serve [--port 7799]           Start web UI
folder-guard log [--n 20]                  Show audit log
```

## Config

Config lives at `~/.config/ai-folder-guard/config.json`. See `config.example.json` for the full schema.

## License

MIT
