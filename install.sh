#!/usr/bin/env bash
set -e

DEST="$HOME/.config/ai-folder-guard"
BIN="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing AI Folder Guard..."

mkdir -p "$DEST" "$BIN"

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

echo ""
echo "Done. Make sure $BIN is in your PATH."
echo ""
echo "Quick start:"
echo "  folder-guard status"
echo "  folder-guard add ~/Documents/Secrets"
echo "  folder-guard install --tool claude-code"
echo "  folder-guard serve   # web UI at http://127.0.0.1:7799"
