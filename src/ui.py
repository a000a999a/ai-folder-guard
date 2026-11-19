#!/usr/bin/env python3
"""AI Folder Guard — web UI (Flask, localhost:7799)."""
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(__file__))
import core
from adapters import claude_code

try:
    from flask import Flask, request, redirect, url_for
except ImportError:
    print("Flask is required: pip install flask", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__)

_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Folder Guard — {{ hostname }}</title>
<style>
:root{--bg:#f5f5f5;--card:#fff;--fg:#1a1a1a;--muted:#666;--border:#ddd;--accent:#2563eb;--danger:#dc2626;--ok:#16a34a;--input-bg:#fff;--host-bg:#1e3a5f;--host-fg:#fff;color-scheme:light}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f0f0f;--card:#1c1c1c;--fg:#e8e8e8;--muted:#999;--border:#333;--accent:#3b82f6;--danger:#ef4444;--ok:#22c55e;--input-bg:#252525;--host-bg:#1e3a5f;--host-fg:#fff;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0f0f0f;--card:#1c1c1c;--fg:#e8e8e8;--muted:#999;--border:#333;--accent:#3b82f6;--danger:#ef4444;--ok:#22c55e;--input-bg:#252525;--host-bg:#1e3a5f;--host-fg:#fff;color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font:14px/1.6 system-ui,sans-serif}
.host-banner{background:var(--host-bg);color:var(--host-fg);padding:20px max(24px,env(safe-area-inset-left,0px));margin-bottom:24px}
.host-banner .machine{font-size:2rem;font-weight:800;letter-spacing:-.02em;line-height:1}
.host-banner .sub{font-size:.85rem;opacity:.7;margin-top:4px}
.content{padding:0 max(16px,env(safe-area-inset-left,0px));padding-bottom:24px}
h1{font-size:1.3rem;font-weight:700;margin-bottom:4px}
.sub{color:var(--muted);font-size:.85rem;margin-bottom:24px}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px}
h2{font-size:.9rem;font-weight:600;margin-bottom:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.row{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}
input[type=text]{flex:1;min-width:0;padding:7px 10px;border:1px solid var(--border);border-radius:6px;background:var(--input-bg);color:var(--fg);font-size:.9rem}
button{padding:7px 14px;border:none;border-radius:6px;cursor:pointer;font-size:.85rem;font-weight:500}
.btn-add{background:var(--accent);color:#fff}
.btn-rm{background:transparent;border:1px solid var(--border);color:var(--fg)}
.btn-rm:hover{border-color:var(--danger);color:var(--danger)}
.pill{display:inline-flex;align-items:center;gap:6px;background:var(--bg);border:1px solid var(--border);border-radius:20px;padding:3px 10px;font-size:.85rem;margin:2px}
.pill form{display:inline}
.pill button{padding:0;background:none;border:none;color:var(--muted);font-size:.9rem;cursor:pointer;line-height:1}
.pill button:hover{color:var(--danger)}
.settings-row{display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.settings-row label{font-size:.9rem;display:flex;align-items:center;gap:6px}
select{padding:5px 8px;border:1px solid var(--border);border-radius:6px;background:var(--input-bg);color:var(--fg);font-size:.9rem}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.75rem;font-weight:600}
.badge.on{background:#dcfce7;color:#15803d}.badge.off{background:#fee2e2;color:#b91c1c}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]) .badge.on{background:#14532d;color:#4ade80}:root:not([data-theme="light"]) .badge.off{background:#450a0a;color:#fca5a5}}
:root[data-theme="dark"] .badge.on{background:#14532d;color:#4ade80}:root[data-theme="dark"] .badge.off{background:#450a0a;color:#fca5a5}
.log{font:12px/1.5 monospace;overflow-x:auto}
.log-row{display:grid;grid-template-columns:170px 140px 1fr;gap:8px;padding:3px 0;border-bottom:1px solid var(--border)}
.log-row:last-child{border:none}
.ts{color:var(--muted)}
</style>
</head>
<body>
<div class="host-banner">
  <div class="machine">{{ hostname }}</div>
  <div class="sub">AI Folder Guard &mdash; filesystem protection for AI coding tools &mdash; <a href="https://github.com/a000a999a/ai-folder-guard" style="color:rgba(255,255,255,.8)">GitHub</a></div>
</div>
<div class="content">

<div class="card">
  <h2>Settings</h2>
  <div class="settings-row">
    <form method="post" action="/set">
      <label>Mode
        <select name="mode" onchange="this.form.submit()">
          <option value="blacklist" {% if cfg.mode=="blacklist" %}selected{% endif %}>Blacklist (block specific)</option>
          <option value="whitelist" {% if cfg.mode=="whitelist" %}selected{% endif %}>Whitelist (allow only specific)</option>
        </select>
      </label>
      <input type="hidden" name="field" value="mode">
    </form>
    <form method="post" action="/set">
      <label>Action
        <select name="action" onchange="this.form.submit()">
          <option value="ask" {% if cfg.action=="ask" %}selected{% endif %}>Ask (prompt)</option>
          <option value="deny" {% if cfg.action=="deny" %}selected{% endif %}>Deny (block)</option>
        </select>
      </label>
      <input type="hidden" name="field" value="action">
    </form>
    <span>Claude Code hook: <span class="badge {% if cc_installed %}on{% else %}off{% endif %}">{% if cc_installed %}installed{% else %}not installed{% endif %}</span></span>
    {% if not cc_installed %}
    <form method="post" action="/install-claude"><button class="btn-add" type="submit">Install hook</button></form>
    {% endif %}
  </div>
</div>

<div class="card">
  <h2>Blocked paths</h2>
  <div>
    {% for p in cfg.blocked %}
    <span class="pill">{{ p }}
      <form method="post" action="/remove"><input type="hidden" name="path" value="{{ p }}"><input type="hidden" name="list" value="blocked"><button title="Remove">&times;</button></form>
    </span>
    {% endfor %}
  </div>
  <form method="post" action="/add" style="margin-top:12px">
    <div class="row">
      <input type="text" name="path" placeholder="~/Documents/Secrets" required>
      <input type="hidden" name="list" value="blocked">
      <button class="btn-add" type="submit">+ Add</button>
    </div>
  </form>
</div>

<div class="card">
  <h2>Allowed paths <span style="font-weight:400;font-size:.8rem;color:var(--muted)">(whitelist mode)</span></h2>
  <div>
    {% for p in cfg.allowed %}
    <span class="pill">{{ p }}
      <form method="post" action="/remove"><input type="hidden" name="path" value="{{ p }}"><input type="hidden" name="list" value="allowed"><button title="Remove">&times;</button></form>
    </span>
    {% endfor %}
  </div>
  <form method="post" action="/add" style="margin-top:12px">
    <div class="row">
      <input type="text" name="path" placeholder="~/Projects" required>
      <input type="hidden" name="list" value="allowed">
      <button class="btn-add" type="submit">+ Add</button>
    </div>
  </form>
</div>

<div class="card">
  <h2>Exempt paths</h2>
  <div>
    {% for p in cfg.exempt %}
    <span class="pill">{{ p }}
      <form method="post" action="/remove"><input type="hidden" name="path" value="{{ p }}"><input type="hidden" name="list" value="exempt"><button title="Remove">&times;</button></form>
    </span>
    {% endfor %}
  </div>
  <form method="post" action="/add" style="margin-top:12px">
    <div class="row">
      <input type="text" name="path" placeholder="~/Documents/Secrets/public" required>
      <input type="hidden" name="list" value="exempt">
      <button class="btn-add" type="submit">+ Add</button>
    </div>
  </form>
</div>

<div class="card">
  <h2>Audit log (last 50)</h2>
  {% if log %}
  <div class="log">
    <div class="log-row" style="font-weight:600"><span>Time</span><span>Tool</span><span>Path / Reason</span></div>
    {% for e in log %}<div class="log-row"><span class="ts">{{ e.ts }}</span><span>{{ e.tool }}</span><span>{{ e.path }}</span></div>{% endfor %}
  </div>
  {% else %}
  <p style="color:var(--muted);font-size:.9rem">No entries yet.</p>
  {% endif %}
</div>
</div>
</body>
</html>"""

from jinja2 import Template


class _Obj:
    def __init__(self, d):
        self.__dict__.update(d)


@app.route("/")
def index():
    cfg = core.load()
    log = core.read_log(50)
    cc_installed = claude_code.is_installed()
    hostname = socket.gethostname()
    t = Template(_HTML)
    return t.render(cfg=_Obj(cfg), log=log, cc_installed=cc_installed, hostname=hostname)


@app.route("/add", methods=["POST"])
def add():
    lst = request.form.get("list", "blocked")
    path = request.form.get("path", "").strip()
    if path:
        cfg = core.load()
        if path not in cfg[lst]:
            cfg[lst].append(path)
            core.save(cfg)
    return redirect(url_for("index"))


@app.route("/remove", methods=["POST"])
def remove():
    lst = request.form.get("list", "blocked")
    path = request.form.get("path", "").strip()
    if path:
        cfg = core.load()
        if path in cfg[lst]:
            cfg[lst].remove(path)
            core.save(cfg)
    return redirect(url_for("index"))


@app.route("/set", methods=["POST"])
def set_field():
    field = request.form.get("field")
    value = request.form.get(field, "").strip()
    if field in ("mode", "action") and value:
        cfg = core.load()
        cfg[field] = value
        core.save(cfg)
    return redirect(url_for("index"))


@app.route("/install-claude", methods=["POST"])
def install_claude():
    claude_code.install()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7799)
