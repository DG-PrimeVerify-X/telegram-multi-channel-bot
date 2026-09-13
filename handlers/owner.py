from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import OWNER_ID
from utils.keyboards import owner_panel, back, admin_panel, channel_panel
from utils.states import AddAdmin, AddChannel, AddContent, AttachContent, AssignChannel, Broadcast
from services.channel_service import verify_channel
from services.broadcast_service import copy_broadcast

router=Router()

def is_owner(uid): return uid == OWNER_ID

@router.message(CommandStart())
async def start(message: Message, db):
    await db.upsert_user(message.from_user)
    if not is_owner(message.from_user.id) and not await db.is_admin(message.from_user.id):
        await message.answer("Welcome. Access is available after an administrator adds you.")
        return
    if is_owner(message.from_user.id):
        await message.answer("👑 <b>OWNER PANEL</b>\n\nWelcome. Choose an option below:", reply_markup=owner_panel())
    else:
        from utils.keyboards import admin_channel_panel
        await message.answer("🛡️ <b>ADMIN PANEL</b>\n\nChoose an option:", reply_markup=admin_channel_panel())

@router.callback_query(F.data=="owner:home")
async def owner_home(c: CallbackQuery):
    if not is_owner(c.from_user.id): return await c.answer("Access denied", show_alert=True)
    await c.message.edit_text("👑 <b>OWNER PANEL</b>\n\nChoose an option:", reply_markup=owner_panel())
    await c.answer()

@router.callback_query(F.data.startswith("owner:"))
async def owner_sections(c: CallbackQuery, db, state: FSMContext):
    if not is_owner(c.from_user.id): return await c.answer("Access denied", show_alert=True)
    sec=c.data.split(":",1)[1]
    if sec=="admins":
        await c.message.edit_text("👥 <b>ADMIN MANAGEMENT</b>\n\nManage admins and permissions.",reply_markup=admin_panel())
    elif sec=="channels":
        await c.message.edit_text("📢 <b>CHANNEL MANAGEMENT</b>\n\nAdd/verify channels and assign admins.",reply_markup=channel_panel())
    elif sec=="users":
        users=await db.all_users()
        await c.message.edit_text(f"👤 <b>USERS</b>\n\nTracked users: <b>{len(users)}</b>",reply_markup=back())
    elif sec=="content":
        items=await db.content_list(c.from_user.id)
        txt="📁 <b>CONTENT / FILES</b>\n\n"
        txt += "\n".join(f"#{r['id']} — {r['title']}" for r in items[:30]) or "No content saved."
        from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
        kb=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add Content",callback_data="content:add")],
            [InlineKeyboardButton(text="🔗 Attach to Channel",callback_data="content:attach")],
            [InlineKeyboardButton(text="🗑 Delete Content",callback_data="content:delete")],
            [InlineKeyboardButton(text="⬅️ Back",callback_data="owner:home")]
        ])
        await c.message.edit_text(txt,reply_markup=kb)
    elif sec=="stats":
        channels=await db.get_channels(); users=await db.all_users(); admins=await db.admin_list()
        await c.message.edit_text(f"📊 <b>STATISTICS</b>\n\nChannels: {len(channels)}\nAdmins: {len(admins)}\nTracked users: {len(users)}",reply_markup=back())
    elif sec=="settings":
        await c.message.edit_text("⚙️ <b>SETTINGS</b>\n\nGlobal credentials stay in .env. Per-channel Auto Accept and Auto DM are configurable under Channels.",reply_markup=back())
    elif sec=="logs":
        rows=await db.fetchall("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 20")
        txt="📝 <b>ACTIVITY LOGS</b>\n\n"+"\n".join(f"{r['created_at']} — {r['action']} — {r['details'] or ''}" for r in rows) or "No logs."
        await c.message.edit_text(txt[:3900],reply_markup=back())
    elif sec=="broadcast":
        from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
        rows=await db.get_channels()
        buttons=[[InlineKeyboardButton(text="🌐 All tracked users",callback_data="btarget:all")]]
        buttons += [[InlineKeyboardButton(text=f"📢 {r['title']} members",callback_data=f"btarget:{r['chat_id']}")] for r in rows]
        buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="owner:home")])
        await c.message.edit_text("📣 <b>BROADCAST TARGET</b>\n\nChoose audience:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await c.answer()

@router.callback_query(F.data=="admin:add")
async def admin_add(c:CallbackQuery,state:FSMContext):
    if not is_owner(c.from_user.id): return await c.answer("Access denied",show_alert=True)
    await state.set_state(AddAdmin.waiting_user)
    await c.message.edit_text("➕ Send the admin's numeric Telegram user ID.")
    await c.answer()

@router.message(AddAdmin.waiting_user)
async def admin_add_id(message:Message,db,state:FSMContext):
    if not is_owner(message.from_user.id): return
    try: uid=int(message.text.strip())
    except: return await message.answer("Send a numeric Telegram user ID.")
    await db.add_admin(uid,None,f"User {uid}")
    for p in ("channels","users","content","broadcast","stats"):
        await db.set_permission(uid,p,True)
    await db.log(message.from_user.id,"add_admin",str(uid))
    await state.clear()
    await message.answer(f"✅ Admin <code>{uid}</code> added with standard permissions.",reply_markup=admin_panel())

@router.callback_query(F.data=="admin:list")
async def admin_list(c:CallbackQuery,db):
    rows=await db.admin_list()
    txt="👥 <b>ADMIN LIST</b>\n\n"+"\n".join(f"• <code>{r['user_id']}</code> — {r['full_name']}" for r in rows) or "No admins."
    await c.message.edit_text(txt,reply_markup=back("owner:admins")); await c.answer()

@router.callback_query(F.data=="admin:perms")
async def admin_perms(c:CallbackQuery,db):
    rows=await db.admin_list()
    if not rows:
        return await c.message.edit_text("No admins.",reply_markup=back("owner:admins"))
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=f"👤 {r['full_name']} ({r['user_id']})",callback_data=f"perms:{r['user_id']}")] for r in rows]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="owner:admins")])
    await c.message.edit_text("🔐 <b>PERMISSIONS</b>\n\nSelect an admin:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("perms:"))
async def perms_detail(c:CallbackQuery,db):
    uid=int(c.data.split(":")[1]); current=await db.permissions(uid)
    perms=["channels","users","content","broadcast","stats"]
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[]
    for p in perms:
        mark="✅" if p in current else "❌"
        buttons.append([InlineKeyboardButton(text=f"{mark} {p.title()}",callback_data=f"toggleperm:{uid}:{p}")])
    buttons += [[InlineKeyboardButton(text="🗑 Remove Admin",callback_data=f"removeadmin:{uid}")],[InlineKeyboardButton(text="⬅️ Back",callback_data="admin:perms")]]
    await c.message.edit_text(f"🔐 <b>PERMISSIONS</b>\nAdmin: <code>{uid}</code>",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("toggleperm:"))
async def toggle_perm(c:CallbackQuery,db):
    _,uid,p=c.data.split(":"); uid=int(uid)
    cur=await db.permissions(uid); await db.set_permission(uid,p,p not in cur)
    await perms_detail(c,db)

@router.callback_query(F.data.startswith("removeadmin:"))
async def remove_admin(c:CallbackQuery,db):
    uid=int(c.data.split(":")[1]); await db.remove_admin(uid); await db.log(c.from_user.id,"remove_admin",str(uid))
    await c.message.edit_text("✅ Admin removed.",reply_markup=admin_panel()); await c.answer()

@router.callback_query(F.data=="channel:add")
async def channel_add(c:CallbackQuery,state:FSMContext):
    await state.set_state(AddChannel.waiting_channel)
    await c.message.edit_text("➕ Send the channel @username or numeric chat ID.\n\nThe bot must already be an administrator there with join-request permission.")
    await c.answer()

@router.message(AddChannel.waiting_channel)
async def channel_add_message(message:Message,bot,db,state:FSMContext):
    ref=message.text.strip()
    try:
        chat,_=await verify_channel(bot,ref)
        await db.add_channel(chat.id,chat.username,chat.title)
        await db.log(message.from_user.id,"add_channel",str(chat.id))
        await state.clear()
        await message.answer(f"✅ Channel added: <b>{chat.title}</b>\nID: <code>{chat.id}</code>",reply_markup=channel_panel())
    except Exception as e:
        await message.answer(f"❌ Channel verification failed.\n{str(e)[:500]}")

@router.callback_query(F.data=="channel:list")
async def channel_list(c:CallbackQuery,db):
    rows=await db.get_channels()
    txt="📋 <b>CHANNELS</b>\n\n"+"\n".join(f"• {r['title']} — <code>{r['chat_id']}</code>\n  AutoAccept: {'ON' if r['auto_accept'] else 'OFF'} | AutoDM: {'ON' if r['auto_dm'] else 'OFF'}" for r in rows) or "No channels."
    await c.message.edit_text(txt,reply_markup=back("owner:channels")); await c.answer()

@router.callback_query(F.data=="channel:settings")
async def channel_settings(c:CallbackQuery,db):
    rows=await db.get_channels()
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=f"⚙️ {r['title']}",callback_data=f"cset:{r['chat_id']}")] for r in rows]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="owner:channels")])
    await c.message.edit_text("⚙️ Select a channel:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("cset:"))
async def cset(c:CallbackQuery,db):
    cid=int(c.data.split(":")[1]); r=await db.get_channel(cid)
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Auto Accept: {'ON' if r['auto_accept'] else 'OFF'}",callback_data=f"ctoggle:{cid}:auto_accept")],
        [InlineKeyboardButton(text=f"Auto DM: {'ON' if r['auto_dm'] else 'OFF'}",callback_data=f"ctoggle:{cid}:auto_dm")],
        [InlineKeyboardButton(text="⬅️ Back",callback_data="channel:settings")]
    ])
    await c.message.edit_text(f"⚙️ <b>{r['title']}</b>",reply_markup=kb); await c.answer()

@router.callback_query(F.data.startswith("ctoggle:"))
async def ctoggle(c:CallbackQuery,db):
    _,cid,field=c.data.split(":"); cid=int(cid); r=await db.get_channel(cid)
    await db.set_channel_option(cid,field,not bool(r[field])); await cset(c,db)

@router.callback_query(F.data=="channel:assign")
async def channel_assign(c:CallbackQuery,db,state:FSMContext):
    rows=await db.get_channels()
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=r["title"],callback_data=f"assignc:{r['chat_id']}")] for r in rows]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="owner:channels")])
    await c.message.edit_text("👥 Select channel to assign:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("assignc:"))
async def assignc(c:CallbackQuery,state:FSMContext):
    await state.update_data(chat_id=int(c.data.split(":")[1])); await state.set_state(AssignChannel.waiting_admin)
    await c.message.edit_text("Send the numeric admin user ID to assign this channel."); await c.answer()

@router.message(AssignChannel.waiting_admin)
async def assign_admin(message:Message,db,state:FSMContext):
    try: aid=int(message.text.strip())
    except: return await message.answer("Send numeric admin ID.")
    data=await state.get_data(); cid=data["chat_id"]
    if not await db.is_admin(aid): return await message.answer("That user is not an active admin.")
    await db.assign_channel(cid,aid); await db.log(message.from_user.id,"assign_channel",f"{cid}->{aid}")
    await state.clear(); await message.answer("✅ Channel assigned.",reply_markup=channel_panel())

@router.callback_query(F.data=="content:add")
async def content_add(c:CallbackQuery,state:FSMContext):
    await state.set_state(AddContent.waiting_message)
    await c.message.edit_text("📁 Send/forward the exact message or file you want to save.\n\nCustom emoji, formatting and Telegram media are preserved using copy_message.")
    await c.answer()

@router.message(AddContent.waiting_message)
async def content_capture(message:Message,state:FSMContext):
    await state.update_data(source_chat_id=message.chat.id,source_message_id=message.message_id)
    await state.set_state(AddContent.waiting_title)
    await message.answer("Give this content a short name/title.")

@router.message(AddContent.waiting_title)
async def content_title(message:Message,db,state:FSMContext):
    data=await state.get_data()
    cid=await db.add_content(message.from_user.id,message.text.strip()[:120],data["source_chat_id"],data["source_message_id"])
    await state.clear()
    await message.answer(f"✅ Content saved as #{cid}.",reply_markup=owner_panel())

@router.callback_query(F.data=="content:attach")
async def content_attach_start(c:CallbackQuery,db,state:FSMContext):
    items=await db.content_list(c.from_user.id)
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=f"#{r['id']} {r['title']}",callback_data=f"attachitem:{r['id']}")] for r in items]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="owner:content")])
    await c.message.edit_text("🔗 Select content:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("attachitem:"))
async def attach_item(c:CallbackQuery,state:FSMContext):
    await state.update_data(content_id=int(c.data.split(":")[1]))
    await state.set_state(AttachContent.waiting_channel)
    await c.message.edit_text("Send the numeric channel ID to attach this content to."); await c.answer()

@router.message(AttachContent.waiting_channel)
async def attach_channel(message:Message,db,state:FSMContext):
    try: cid=int(message.text.strip())
    except: return await message.answer("Send numeric channel ID.")
    data=await state.get_data()
    if not await db.get_channel(cid): return await message.answer("Channel not found.")
    await db.attach_content(cid,data["content_id"])
    await state.clear(); await message.answer("✅ Content attached. It will be sent on approved join requests.",reply_markup=owner_panel())

@router.callback_query(F.data=="content:delete")
async def content_delete_start(c:CallbackQuery,db):
    items=await db.content_list(c.from_user.id)
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
    buttons=[[InlineKeyboardButton(text=f"🗑 #{r['id']} {r['title']}",callback_data=f"delcontent:{r['id']}")] for r in items]
    buttons.append([InlineKeyboardButton(text="⬅️ Back",callback_data="owner:content")])
    await c.message.edit_text("Select content to delete:",reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)); await c.answer()

@router.callback_query(F.data.startswith("delcontent:"))
async def content_delete(c:CallbackQuery,db):
    cid=int(c.data.split(":")[1]); await db.delete_content(cid); await c.message.edit_text("✅ Content deleted.",reply_markup=owner_panel()); await c.answer()

@router.callback_query(F.data.startswith("btarget:"))
async def broadcast_target(c:CallbackQuery,state:FSMContext,db):
    target=c.data.split(":",1)[1]
    await state.update_data(target=target); await state.set_state(Broadcast.waiting_message)
    label="all tracked users" if target=="all" else f"channel {target} members"
    await c.message.edit_text(f"📣 Target: <b>{label}</b>\n\nNow send the message/media to broadcast."); await c.answer()

@router.message(Broadcast.waiting_message)
async def broadcast_message(message:Message,bot,db,state:FSMContext):
    data=await state.get_data(); target=data.get("target","all")
    users=await db.all_users() if target=="all" else await db.channel_users(int(target))
    await message.answer(f"📣 Broadcasting to {len(users)} tracked users...")
    sent,failed=await copy_broadcast(bot,db,message.from_user.id,message.chat.id,message.message_id,[u["user_id"] for u in users],label="broadcast")
    await state.clear()
    await message.answer(f"✅ Broadcast finished.\nSent: {sent}\nFailed: {failed}",reply_markup=owner_panel())
