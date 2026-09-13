# Telegram Multi-Channel Bot — Final Build

A modular aiogram 3 bot with Telegram inline GUI.

## Included
- Owner panel
- Admin management + per-admin permissions
- Multi-channel management and admin assignment
- Join-request auto accept
- Per-channel auto DM ON/OFF
- Content/file manager using Telegram `copy_message` source references
- Broadcast to tracked users
- User tracking
- Statistics
- Activity logs
- Channel isolation for admins
- SQLite + WAL
- `.env` secret protection
- systemd deployment template

## Important Telegram requirements
1. The bot must be an administrator in each managed channel.
2. For join requests, the bot needs permission to invite users / manage join requests.
3. A user must have interacted with the bot before the bot can DM them. Join-request users are tracked when the bot receives the request.
4. Never commit `.env`, the database, or logs.

## Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python bot.py
```

For production use the supplied `deploy/telegram-bot.service`.
