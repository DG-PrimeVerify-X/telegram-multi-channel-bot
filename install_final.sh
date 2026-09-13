#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="/opt/telegram-bot-github"

echo "== Telegram Multi-Channel Bot: final installer =="
if [ "$APP_DIR" != "$TARGET" ]; then
  echo "Run this installer from $TARGET after extracting the final build."
  exit 1
fi

mkdir -p "$TARGET/data" "$TARGET/logs"
[ -f "$TARGET/.env" ] && cp "$TARGET/.env" "$TARGET/.env.backup.$(date +%Y%m%d%H%M%S)"
[ -f "$TARGET/data/bot.db" ] && cp "$TARGET/data/bot.db" "$TARGET/data/bot.db.backup.$(date +%Y%m%d%H%M%S)"

python3 -m venv "$TARGET/venv" 2>/dev/null || true
"$TARGET/venv/bin/python" -m pip install --upgrade pip >/dev/null
"$TARGET/venv/bin/pip" install -r "$TARGET/requirements.txt"

"$TARGET/venv/bin/python" -m compileall -q "$TARGET"
echo "Code syntax check: OK"

if [ ! -f "$TARGET/.env" ]; then
  cp "$TARGET/.env.example" "$TARGET/.env"
  echo
  echo "IMPORTANT: edit $TARGET/.env and set BOT_TOKEN + OWNER_ID."
fi

cat > /etc/systemd/system/telegram-multi-channel-bot.service <<EOF
[Unit]
Description=Telegram Multi-Channel Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$TARGET
ExecStart=$TARGET/venv/bin/python $TARGET/bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable telegram-multi-channel-bot >/dev/null
echo
echo "FINAL BUILD INSTALLED."
echo "Next: nano $TARGET/.env"
echo "Then: systemctl restart telegram-multi-channel-bot"
echo "Logs: journalctl -u telegram-multi-channel-bot -f"
