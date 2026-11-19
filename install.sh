#!/usr/bin/env bash
set -e

DEST="$HOME/.config/ai-folder-guard"
BIN="$HOME/.local/bin"
SYSTEMD="$HOME/.config/systemd/user"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing AI Folder Guard..."

mkdir -p "$DEST" "$BIN" "$SYSTEMD"

cp -r "$SCRIPT_DIR/src/"* "$DEST/"
chmod +x "$DEST/hook.py"

if [ ! -f "$DEST/config.json" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$DEST/config.json"
    echo "Created default config at $DEST/config.json"
fi

cat > "$BIN/folder-guard" << EOF
#!/usr/bin/env bash
exec python3 -I "$DEST/cli.py" "\$@"
EOF
chmod +x "$BIN/folder-guard"

# systemd user service
cat > "$SYSTEMD/ai-folder-guard.service" << EOF
[Unit]
Description=AI Folder Guard web UI
After=network.target

[Service]
ExecStart=$(which python3) -I $DEST/cli.py serve
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now ai-folder-guard.service
echo "Web UI service started (port 7799)."

echo ""
echo "Done. Make sure $BIN is in your PATH."
echo ""
echo "Quick start:"
echo "  folder-guard status"
echo "  folder-guard add ~/Documents/Secrets"
echo "  folder-guard install --tool claude-code"
LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}' || echo "localhost")
echo "  Web UI: http://$LOCAL_IP:7799"
