#!/bin/bash
# Installs a LaunchAgent to start SongSearch2 automatically at login on macOS.

set -e

PLIST_NAME="com.songsearch2.launch.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

mkdir -p "$LAUNCH_AGENTS_DIR"

python_path="$(command -v python3)"
repo_path="$(cd "$(dirname "$0")/.." && pwd)"

cat > "$DEST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.songsearch2</string>
    <key>ProgramArguments</key>
    <array>
        <string>${python_path}</string>
        <string>-m</string>
        <string>songsearch</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${repo_path}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/songsearch2.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/songsearch2.err</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$UID" "$DEST" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$DEST"

echo "LaunchAgent installed to $DEST"
