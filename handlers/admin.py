from aiogram import Router,F
from aiogram.types import Message,CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.keyboards import admin_channel_panel
from utils.states import AdminContent,AdminBroadcast
from services.broadcast_service import copy_broadcast
router=Router()

@router.callback_query(F.data=="admin:menu")
async def admin_menu(c:CallbackQuery,db):
    if not await db.is_admin(c.from_user.id): return await c.answer("Access denied",show_alert=True)
    await c.message.edit_text("🛡️ <b>ADMIN PANEL</b>\n\nChoose an option:",reply_markup=admin_channel_panel()); await c.answer()

@router.callback_query(F.data=="ach:list")
async def my_channels(c:CallbackQuery,db):
    rows=await db.get_admin_channels(c.from_user.id)
    txt="📋 <b>MY CHANNELS</b>\n\n"+"\n".join(f"• {r['title']} — <code>{r['chat_id']}</code>" for r in rows) or "No channels assigned."
    await c.message.edit_text(txt,reply_markup=admin_channel_panel()); await c.answer()

@router.callback_query(F.data=="ach:content")
async def ach_content(c:CallbackQuery,db):
    if not await db.has_permission(c.from_user.id,"content"): return await c.answer("No permission",show_alert=True)
    rows=await db.get_admin_channels(c.from_user.id)
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=f"📁 {r['title']}",callback_data=f"admincontent:{r['chat_id']}")] for r in rows]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="admin:menu")])
    await c.message.edit_text("📁 Select an assigned channel:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("admincontent:"))
async def admin_content_start(c:CallbackQuery,state:FSMContext,db):
    cid=int(c.data.split(":")[1])
    allowed=[r["chat_id"] for r in await db.get_admin_channels(c.from_user.id)]
    if cid not in allowed: return await c.answer("Channel not assigned",show_alert=True)
    await state.update_data(chat_id=cid); await state.set_state(AdminContent.waiting_message)
    await c.message.edit_text("📁 Send the message/file to save for this channel's auto-DM.")
    await c.answer()

@router.message(AdminContent.waiting_message)
async def admin_content_capture(m:Message,state:FSMContext):
    await state.update_data(source_chat_id=m.chat.id,source_message_id=m.message_id)
    await state.set_state(AdminContent.waiting_title)
    await m.answer("Give this content a title.")

@router.message(AdminContent.waiting_title)
async def admin_content_title(m:Message,db,state:FSMContext):
    d=await state.get_data()
    item=await db.add_content(m.from_user.id,m.text.strip()[:120],d["source_chat_id"],d["source_message_id"])
    await db.attach_content(d["chat_id"],item)
    await db.log(m.from_user.id,"admin_add_content",f"channel={d['chat_id']}, content={item}")
    await state.clear(); await m.answer("✅ Content saved and attached to the channel.",reply_markup=admin_channel_panel())

@router.callback_query(F.data=="ach:broadcast")
async def ach_broadcast(c:CallbackQuery,db):
    if not await db.has_permission(c.from_user.id,"broadcast"): return await c.answer("No permission",show_alert=True)
    rows=await db.get_admin_channels(c.from_user.id)
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=f"📣 {r['title']}",callback_data=f"adminbroadcast:{r['chat_id']}")] for r in rows]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="admin:menu")])
    await c.message.edit_text("📣 Select channel audience:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("adminbroadcast:"))
async def admin_broadcast_start(c:CallbackQuery,state:FSMContext,db):
    cid=int(c.data.split(":")[1])
    allowed=[r["chat_id"] for r in await db.get_admin_channels(c.from_user.id)]
    if cid not in allowed: return await c.answer("Channel not assigned",show_alert=True)
    await state.update_data(chat_id=cid); await state.set_state(AdminBroadcast.waiting_message)
    await c.message.edit_text("📣 Send the message/media to broadcast to tracked members of this channel."); await c.answer()

@router.message(AdminBroadcast.waiting_message)
async def admin_broadcast(m:Message,bot,db,state:FSMContext):
    d=await state.get_data(); users=await db.channel_users(d["chat_id"])
    await m.answer(f"📣 Broadcasting to {len(users)} tracked channel members...")
    sent,failed=await copy_broadcast(bot,db,m.from_user.id,m.chat.id,m.message_id,[u["user_id"] for u in users],label="admin_broadcast")
    await state.clear(); await m.answer(f"✅ Done. Sent: {sent} | Failed: {failed}",reply_markup=admin_channel_panel())

@router.callback_query(F.data=="ach:stats")
async def ach_stats(c:CallbackQuery,db):
    rows=await db.get_admin_channels(c.from_user.id)
    total=0
    for r in rows: total += len(await db.channel_users(r["chat_id"]))
    await c.message.edit_text(f"📊 <b>MY STATISTICS</b>\n\nChannels: {len(rows)}\nChannel members tracked: {total}",reply_markup=admin_channel_panel()); await c.answer()
