import aiosqlite
from typing import Optional

class DB:
    def __init__(self, path: str):
        self.path = path

    async def execute(self, sql, params=()):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(sql, params)
            await db.commit()
            return cur

    async def fetchone(self, sql, params=()):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(sql, params)
            return await cur.fetchone()

    async def fetchall(self, sql, params=()):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(sql, params)
            return await cur.fetchall()

    async def log(self, actor_id, action, details=""):
        await self.execute(
            "INSERT INTO activity_logs(actor_id,action,details) VALUES(?,?,?)",
            (actor_id, action, details)
        )

    async def upsert_user(self, user):
        await self.execute("""
        INSERT INTO users(user_id,username,full_name,is_bot,interacted,last_seen)
        VALUES(?,?,?,?,1,CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
          username=excluded.username, full_name=excluded.full_name,
          is_bot=excluded.is_bot, interacted=1, last_seen=CURRENT_TIMESTAMP
        """, (user.id, user.username, user.full_name, int(user.is_bot)))

    async def get_channel(self, chat_id):
        return await self.fetchone("SELECT * FROM channels WHERE chat_id=?", (chat_id,))

    async def get_channels(self):
        return await self.fetchall("SELECT * FROM channels WHERE active=1 ORDER BY title")

    async def get_admin_channels(self, admin_id):
        return await self.fetchall("""
        SELECT c.* FROM channels c
        JOIN channel_admins ca ON ca.chat_id=c.chat_id
        WHERE ca.admin_id=? AND c.active=1 ORDER BY c.title
        """, (admin_id,))

    async def is_admin(self, user_id):
        r=await self.fetchone("SELECT active FROM admins WHERE user_id=?", (user_id,))
        return bool(r and r["active"])

    async def has_permission(self, user_id, permission):
        r=await self.fetchone("""
        SELECT 1 FROM admin_permissions WHERE user_id=? AND permission=?
        """, (user_id, permission))
        return bool(r)

    async def admin_list(self):
        return await self.fetchall("SELECT * FROM admins WHERE active=1 ORDER BY created_at DESC")

    async def add_admin(self, user_id, username, full_name):
        await self.execute("""
        INSERT INTO admins(user_id,username,full_name,active) VALUES(?,?,?,1)
        ON CONFLICT(user_id) DO UPDATE SET active=1, username=excluded.username, full_name=excluded.full_name
        """, (user_id, username, full_name))

    async def remove_admin(self, user_id):
        await self.execute("UPDATE admins SET active=0 WHERE user_id=?", (user_id,))
        await self.execute("DELETE FROM admin_permissions WHERE user_id=?", (user_id,))

    async def set_permission(self, user_id, permission, enabled):
        if enabled:
            await self.execute("INSERT OR IGNORE INTO admin_permissions(user_id,permission) VALUES(?,?)",(user_id,permission))
        else:
            await self.execute("DELETE FROM admin_permissions WHERE user_id=? AND permission=?",(user_id,permission))

    async def permissions(self, user_id):
        rows=await self.fetchall("SELECT permission FROM admin_permissions WHERE user_id=?",(user_id,))
        return {r["permission"] for r in rows}

    async def add_channel(self, chat_id, username, title):
        await self.execute("""
        INSERT INTO channels(chat_id,username,title) VALUES(?,?,?)
        ON CONFLICT(chat_id) DO UPDATE SET username=excluded.username,title=excluded.title,active=1
        """,(chat_id,username,title))

    async def set_channel_option(self, chat_id, field, value):
        if field not in {"auto_accept","auto_dm"}: raise ValueError("bad field")
        await self.execute(f"UPDATE channels SET {field}=? WHERE chat_id=?",(int(value),chat_id))

    async def assign_channel(self, chat_id, admin_id):
        await self.execute("INSERT OR IGNORE INTO channel_admins(chat_id,admin_id) VALUES(?,?)",(chat_id,admin_id))

    async def remove_channel(self, chat_id):
        await self.execute("UPDATE channels SET active=0 WHERE chat_id=?",(chat_id,))

    async def add_content(self, owner_id, title, source_chat_id, source_message_id):
        cur=await self.execute("""
        INSERT INTO content_items(owner_id,title,source_chat_id,source_message_id)
        VALUES(?,?,?,?)
        """,(owner_id,title,source_chat_id,source_message_id))
        return cur.lastrowid

    async def attach_content(self, chat_id, content_id):
        row=await self.fetchone("SELECT COALESCE(MAX(position),-1)+1 p FROM channel_content WHERE chat_id=?",(chat_id,))
        await self.execute("INSERT OR IGNORE INTO channel_content(chat_id,content_id,position) VALUES(?,?,?)",(chat_id,content_id,row["p"]))

    async def get_channel_content(self, chat_id):
        return await self.fetchall("""
        SELECT ci.* FROM content_items ci
        JOIN channel_content cc ON cc.content_id=ci.id
        WHERE cc.chat_id=? AND ci.active=1 ORDER BY cc.position, ci.id
        """,(chat_id,))

    async def content_list(self, owner_id=None):
        if owner_id:
            return await self.fetchall("SELECT * FROM content_items WHERE active=1 AND owner_id=? ORDER BY id DESC",(owner_id,))
        return await self.fetchall("SELECT * FROM content_items WHERE active=1 ORDER BY id DESC")

    async def delete_content(self, content_id):
        await self.execute("UPDATE content_items SET active=0 WHERE id=?",(content_id,))
        await self.execute("DELETE FROM channel_content WHERE content_id=?",(content_id,))

    async def all_users(self):
        return await self.fetchall("SELECT * FROM users WHERE interacted=1 AND is_bot=0 ORDER BY user_id")

    async def channel_users(self, chat_id):
        return await self.fetchall("""
        SELECT u.* FROM users u JOIN channel_users cu ON cu.user_id=u.user_id
        WHERE cu.chat_id=? AND u.interacted=1 AND u.is_bot=0
        """,(chat_id,))

    async def add_channel_user(self, chat_id, user_id, status="joined"):
        await self.execute("""
        INSERT INTO channel_users(chat_id,user_id,status) VALUES(?,?,?)
        ON CONFLICT(chat_id,user_id) DO UPDATE SET status=excluded.status
        """,(chat_id,user_id,status))
