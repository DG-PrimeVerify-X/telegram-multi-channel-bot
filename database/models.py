import aiosqlite
from pathlib import Path

DB_PATH = Path("data/bot.db")

async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS bot_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            owner_id INTEGER,
            bot_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admin_permissions (
            admin_id INTEGER PRIMARY KEY,
            manage_channels INTEGER DEFAULT 0,
            manage_users INTEGER DEFAULT 0,
            manage_files INTEGER DEFAULT 0,
            broadcast INTEGER DEFAULT 0,
            statistics INTEGER DEFAULT 0,
            settings INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            title TEXT NOT NULL,
            added_by INTEGER,
            is_verified INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            auto_accept INTEGER DEFAULT 1,
            auto_dm INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS channel_admins (
            channel_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            PRIMARY KEY (channel_id, admin_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS channel_users (
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (channel_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS content_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            source_chat_id INTEGER NOT NULL,
            source_message_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            position INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            source_chat_id INTEGER NOT NULL,
            source_message_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            total INTEGER DEFAULT 0,
            sent INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS broadcast_recipients (
            broadcast_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            error TEXT,
            sent_at TEXT,
            PRIMARY KEY (broadcast_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_channel_users
            ON channel_users(channel_id);
        CREATE INDEX IF NOT EXISTS idx_content_channel
            ON content_items(channel_id);
        """)
        await db.commit()
