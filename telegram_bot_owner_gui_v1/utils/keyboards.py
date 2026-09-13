from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def owner_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Channels", callback_data="owner:channels"),
            InlineKeyboardButton(text="👥 Admins", callback_data="owner:admins"),
        ],
        [
            InlineKeyboardButton(text="👤 Users", callback_data="owner:users"),
            InlineKeyboardButton(text="📁 Content / Files", callback_data="owner:content"),
        ],
        [
            InlineKeyboardButton(text="📣 Broadcast", callback_data="owner:broadcast"),
            InlineKeyboardButton(text="📊 Statistics", callback_data="owner:stats"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Settings", callback_data="owner:settings"),
            InlineKeyboardButton(text="📝 Activity Logs", callback_data="owner:logs"),
        ],
    ])

def back_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Owner Panel", callback_data="owner:home")]
    ])
