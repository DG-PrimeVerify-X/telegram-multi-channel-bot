from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def owner_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Channels", callback_data="owner:channels"),
         InlineKeyboardButton(text="👥 Admins", callback_data="owner:admins")],
        [InlineKeyboardButton(text="👤 Users", callback_data="owner:users"),
         InlineKeyboardButton(text="📁 Content / Files", callback_data="owner:content")],
        [InlineKeyboardButton(text="📣 Broadcast", callback_data="owner:broadcast"),
         InlineKeyboardButton(text="📊 Statistics", callback_data="owner:stats")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="owner:settings"),
         InlineKeyboardButton(text="📝 Activity Logs", callback_data="owner:logs")],
    ])

def back_home():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Owner Panel", callback_data="owner:home")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Admin", callback_data="admin:add"),
         InlineKeyboardButton(text="👥 Admin List", callback_data="admin:list")],
        [InlineKeyboardButton(text="🔐 Permissions", callback_data="admin:permissions")],
        [InlineKeyboardButton(text="⬅️ Owner Panel", callback_data="owner:home")],
    ])

def admin_list_buttons(admins):
    rows = []
    for a in admins:
        label = a[2] or a[1] or str(a[0])
        rows.append([InlineKeyboardButton(text=f"👤 {label}", callback_data=f"admin:view:{a[0]}")])
    rows.append([InlineKeyboardButton(text="⬅️ Admin Menu", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_actions(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Permissions", callback_data=f"admin:perms:{user_id}")],
        [InlineKeyboardButton(text="❌ Remove Admin", callback_data=f"admin:remove:{user_id}")],
        [InlineKeyboardButton(text="⬅️ Admin List", callback_data="admin:list")],
    ])

PERMISSIONS = [
    ("channels", "📢 Channels"),
    ("users", "👤 Users"),
    ("content", "📁 Content"),
    ("broadcast", "📣 Broadcast"),
    ("stats", "📊 Statistics"),
    ("settings", "⚙️ Settings"),
]

def permission_buttons(user_id: int, enabled: set[str]):
    rows = []
    for key, label in PERMISSIONS:
        mark = "✅" if key in enabled else "❌"
        rows.append([InlineKeyboardButton(
            text=f"{mark} {label}",
            callback_data=f"admin:toggle:{user_id}:{key}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Admin", callback_data=f"admin:view:{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
