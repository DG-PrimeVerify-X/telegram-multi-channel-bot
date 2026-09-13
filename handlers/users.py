from aiogram import Router,F
from aiogram.types import Message,CallbackQuery
from utils.keyboards import owner_panel,back
router=Router()

@router.message()
async def track_all_messages(message:Message,db):
    await db.upsert_user(message.from_user)
