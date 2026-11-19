#!/usr/bin/env python3
"""AI Folder Guard — CLI."""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import core
from adapters import claude_code, ignore_file, shell_guards, git_hooks


def cmd_add(args):
    cfg = core.load()
    p = args.path
    key = "blocked" if cfg["mode"] == "blacklist" else "allowed"
    if p not in cfg[key]:
        cfg[key].append(p)
        core.save(cfg)
        print(f"Added '{p}' to {key}.")
    else:
        print(f"'{p}' already in {key}.")


def cmd_remove(args):
    cfg = core.load()
    p = args.path
    for key in ("blocked", "allowed"):
        if p in cfg[key]:
            cfg[key].remove(p)
            core.save(cfg)
            print(f"Removed '{p}' from {key}.")
            return
    print(f"'{p}' not found.")


def cmd_exempt(args):
    cfg = core.load()
    if args.exempt_cmd == "add":
        if args.path not in cfg["exempt"]:
            cfg["exempt"].append(args.path)
            core.save(cfg)
            print(f"Added '{args.path}' to exemptions.")
        else:
            print(f"'{args.path}' already exempt.")
    elif args.exempt_cmd == "remove":
        if args.path in cfg["exempt"]:
            cfg["exempt"].remove(args.path)
            core.save(cfg)
            print(f"Removed '{args.path}' from exemptions.")
        else:
            print(f"'{args.path}' not in exemptions.")


def cmd_list(args):
    cfg = core.load()
    print(f"Mode:   {cfg['mode']}")
    print(f"Action: {cfg['action']}")
    print(f"\nBlocked ({len(cfg['blocked'])}):")
    for p in cfg["blocked"]:
        print(f"  {p}")
    print(f"\nAllowed ({len(cfg['allowed'])}):")
    for p in cfg["allowed"]:
        print(f"  {p}")
    print(f"\nExempt ({len(cfg['exempt'])}):")
    for p in cfg["exempt"]:
        print(f"  {p}")


def cmd_mode(args):
    cfg = core.load()
    if args.value not in ("blacklist", "whitelist"):
        print("Mode must be 'blacklist' or 'whitelist'.")
        sys.exit(1)
    cfg["mode"] = args.value
    core.save(cfg)
    print(f"Mode set to '{args.value}'.")


def cmd_action(args):
    cfg = core.load()
    if args.value not in ("ask", "deny"):
        print("Action must be 'ask' or 'deny'.")
        sys.exit(1)
    cfg["action"] = args.value
    core.save(cfg)
    print(f"Action set to '{args.value}'.")


def cmd_status(args):
    cfg = core.load()
    cc = claude_code.is_installed()
    sg = shell_guards.status()
    gh = git_hooks.status()
    print(f"Config: {core.CONFIG_FILE}")
    print(f"Mode:   {cfg['mode']}")
    print(f"Action: {cfg['action']}")
    print(f"Blocked paths: {len(cfg['blocked'])}")
    print(f"Allowed paths: {len(cfg['allowed'])}")
    print(f"Exempt paths:  {len(cfg['exempt'])}")
    print(f"Claude Code hook: {'installed' if cc else 'not installed'}")
    for cmd, active in sg.items():
        print(f"Shell guard ({cmd}): {'installed' if active else 'not installed'}")
    for hook, active in gh.items():
        print(f"Git hook ({hook}): {'installed' if active else 'not installed'}")


def cmd_install(args):
    tools = args.tool if args.tool != ["all"] else \
        ["claude-code", "shell-guards", "git-hooks"]
    for tool in tools:
        if tool == "claude-code":
            claude_code.install()
            print("Claude Code hook installed.")
        elif tool == "shell-guards":
            installed = shell_guards.install()
            if installed:
                print(f"Shell guards installed for: {', '.join(installed)}")
            else:
                print("Shell guards: nothing new to install.")
        elif tool == "git-hooks":
            ok = git_hooks.install()
            print("Global git hooks installed." if ok else "Git hooks: skipped (see warnings above).")
        elif tool in ("cursor", "copilot", "aider", "continue", "cline"):
            project = args.project or os.getcwd()
            out = ignore_file.write(project, tool)
            print(f"Wrote {out}")
        else:
            print(f"Unknown tool: {tool}")


def cmd_uninstall(args):
    tools = args.tool if args.tool != ["all"] else \
        ["claude-code", "shell-guards", "git-hooks"]
    for tool in tools:
        if tool == "claude-code":
            claude_code.uninstall()
            print("Claude Code hook removed.")
        elif tool == "shell-guards":
            removed = shell_guards.uninstall()
            print(f"Shell guards removed: {', '.join(removed) if removed else 'none found'}.")
        elif tool == "git-hooks":
            git_hooks.uninstall()
            print("Global git hooks removed.")
        else:
            print(f"Uninstall for '{tool}' not supported (delete the ignore file manually).")


def cmd_serve(args):
    port = args.port or 7799
    host = args.host or "127.0.0.1"
    import ui
    ui.app.run(host=host, port=port)


def cmd_log(args):
    n = args.n or 20
    entries = core.read_log(n)
    if not entries:
        print("No log entries.")
        return
    for e in entries:
        print(f"{e['ts']}  {e['tool']:20s}  {e['path']}")


def main():
    p = argparse.ArgumentParser(prog="folder-guard", description="AI Folder Guard")
    sub = p.add_subparsers(dest="cmd")

    pa = sub.add_parser("add", help="Add a path to the blocked/allowed list")
    pa.add_argument("path")

    pr = sub.add_parser("remove", help="Remove a path from the blocked/allowed list")
    pr.add_argument("path")

    pe = sub.add_parser("exempt", help="Manage exemptions")
    pe.add_argument("exempt_cmd", choices=["add", "remove"])
    pe.add_argument("path")

    sub.add_parser("list", help="List all configured paths")

    pm = sub.add_parser("mode", help="Set mode: blacklist or whitelist")
    pm.add_argument("value", choices=["blacklist", "whitelist"])

    pac = sub.add_parser("action", help="Set action: ask or deny")
    pac.add_argument("value", choices=["ask", "deny"])

    sub.add_parser("status", help="Show status")

    pi = sub.add_parser("install", help="Install adapter(s)")
    pi.add_argument("--tool", nargs="+", default=["claude-code"],
                    choices=["claude-code", "shell-guards", "git-hooks",
                             "cursor", "copilot", "aider", "continue", "cline", "all"])
    pi.add_argument("--project", help="Project dir for ignore-file adapters (default: cwd)")

    pu = sub.add_parser("uninstall", help="Uninstall adapter(s)")
    pu.add_argument("--tool", nargs="+", default=["claude-code"],
                    choices=["claude-code", "shell-guards", "git-hooks", "all"])

    ps = sub.add_parser("serve", help="Start web UI")
    ps.add_argument("--port", type=int, default=7799)
    ps.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")

    pl = sub.add_parser("log", help="Show audit log")
    pl.add_argument("--n", type=int, default=20)

    args = p.parse_args()
    dispatch = {
        "add": cmd_add, "remove": cmd_remove, "exempt": cmd_exempt,
        "list": cmd_list, "mode": cmd_mode, "action": cmd_action,
        "status": cmd_status, "install": cmd_install, "uninstall": cmd_uninstall,
        "serve": cmd_serve, "log": cmd_log,
    }
    fn = dispatch.get(args.cmd)
    if fn:
        fn(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
