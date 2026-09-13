from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import OWNER_ID
from utils.keyboards import owner_panel, back_home

router = Router()

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

@router.message(CommandStart())
async def start(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("⛔ Access denied.")
        return
    await message.answer(
        "👑 <b>OWNER PANEL</b>\n\nWelcome. Choose an option below:",
        reply_markup=owner_panel(),
    )

@router.callback_query(F.data == "owner:home")
async def home(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    await callback.message.edit_text(
        "👑 <b>OWNER PANEL</b>\n\nChoose an option below:",
        reply_markup=owner_panel(),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("owner:"))
async def section(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    section_name = callback.data.split(":", 1)[1]
    if section_name == "admins":
        return
    titles = {
        "channels": "📢 <b>CHANNELS</b>\n\nChannel management module will be connected next.",
        "users": "👤 <b>USERS</b>\n\nUser management module will be connected next.",
        "content": "📁 <b>CONTENT / FILES</b>\n\nContent manager will be connected next.",
        "broadcast": "📣 <b>BROADCAST</b>\n\nBroadcast manager will be connected next.",
        "stats": "📊 <b>STATISTICS</b>\n\nStatistics module will be connected next.",
        "settings": "⚙️ <b>SETTINGS</b>\n\nBot settings will be connected next.",
        "logs": "📝 <b>ACTIVITY LOGS</b>\n\nActivity log module will be connected next.",
    }
    await callback.message.edit_text(
        titles.get(section_name, "Unknown section."),
        reply_markup=back_home(),
    )
    await callback.answer()
