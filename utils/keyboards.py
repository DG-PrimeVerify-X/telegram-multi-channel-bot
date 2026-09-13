from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=d) for t,d in row] for row in rows
    ])

def owner_panel():
    return kb([
        [("📢 Channels","owner:channels"),("👥 Admins","owner:admins")],
        [("👤 Users","owner:users"),("📁 Content / Files","owner:content")],
        [("📣 Broadcast","owner:broadcast"),("📊 Statistics","owner:stats")],
        [("⚙️ Settings","owner:settings"),("📝 Activity Logs","owner:logs")],
    ])

def back(data="owner:home"):
    return kb([[("⬅️ Back",data)]])

def admin_panel():
    return kb([
        [("➕ Add Admin","admin:add"),("👥 Admin List","admin:list")],
        [("🔐 Permissions","admin:perms")],
        [("⬅️ Owner Panel","owner:home")]
    ])

def channel_panel():
    return kb([
        [("➕ Add Channel","channel:add"),("📋 Channel List","channel:list")],
        [("⚙️ Channel Settings","channel:settings")],
        [("👥 Assign Admin","channel:assign")],
        [("⬅️ Owner Panel","owner:home")]
    ])

def admin_channel_panel():
    return kb([
        [("📋 My Channels","ach:list")],
        [("📁 Content","ach:content"),("📣 Broadcast","ach:broadcast")],
        [("📊 Statistics","ach:stats")],
        [("⬅️ Admin Panel","admin:menu")]
    ])
