import aiosqlite
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter

from config import OWNER_ID
from database.models import DB_PATH
from utils.keyboards import admin_menu, admin_list_buttons, admin_actions, permission_buttons, PERMISSIONS
from utils.states import AdminAddState

router = Router()

def owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def get_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id, username, full_name, is_active FROM admins ORDER BY created_at DESC"
        )
        return await cur.fetchall()

async def get_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id, username, full_name, is_active, created_at FROM admins WHERE user_id=?",
            (user_id,)
        )
        return await cur.fetchone()

async def get_permissions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT permission FROM admin_permissions WHERE user_id=? AND enabled=1",
            (user_id,)
        )
        return {r[0] for r in await cur.fetchall()}

@router.callback_query(F.data == "owner:admins")
async def open_admins(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await callback.message.edit_text(
        "👥 <b>ADMIN MANAGEMENT</b>\n\nManage admins and their permissions.",
        reply_markup=admin_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "admin:menu")
async def admin_home(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    await callback.message.edit_text(
        "👥 <b>ADMIN MANAGEMENT</b>\n\nChoose an option:",
        reply_markup=admin_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "admin:list")
async def admin_list(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    admins = await get_admins()
    if not admins:
        text = "👥 <b>ADMIN LIST</b>\n\nNo admins added yet."
    else:
        text = "👥 <b>ADMIN LIST</b>\n\nSelect an admin:"
    await callback.message.edit_text(text, reply_markup=admin_list_buttons(admins))
    await callback.answer()

@router.callback_query(F.data == "admin:add")
async def add_start(callback: CallbackQuery, state: FSMContext):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    await state.set_state(AdminAddState.waiting_for_user)
    await callback.message.edit_text(
        "➕ <b>ADD ADMIN</b>\n\n"
        "Forward any message from the person you want to add.\n"
        "Telegram will use the forwarded sender ID when available.\n\n"
        "Send /cancel to stop."
    )
    await callback.answer()

@router.message(StateFilter(AdminAddState.waiting_for_user))
async def add_receive(message: Message, state: FSMContext):
    if not owner(message.from_user.id):
        return
    if message.text and message.text.lower() == "/cancel":
        await state.clear()
        await message.answer("Cancelled.", reply_markup=admin_menu())
        return

    user_id = None
    username = None
    full_name = None

    origin = getattr(message, "forward_origin", None)
    sender_user = getattr(origin, "sender_user", None) if origin else None
    if sender_user:
        user_id = sender_user.id
        username = sender_user.username
        full_name = sender_user.full_name

    if user_id is None and message.from_user and message.from_user.id != OWNER_ID:
        # A direct message from the owner cannot reveal another user's ID;
        # forwarding is the reliable GUI route.
        await message.answer(
            "⚠️ Please <b>forward a message from the user</b> you want to add, "
            "then send it again."
        )
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO admins(user_id, username, full_name, is_active) VALUES(?,?,?,1)",
            (user_id, username, full_name)
        )
        await db.commit()
    await state.clear()
    await message.answer(
        f"✅ Admin added.\nUser ID: <code>{user_id}</code>",
        reply_markup=admin_menu()
    )

@router.callback_query(F.data.startswith("admin:view:"))
async def view_admin(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    user_id = int(callback.data.split(":")[2])
    a = await get_admin(user_id)
    if not a:
        await callback.answer("Admin not found.", show_alert=True); return
    perms = await get_permissions(user_id)
    perm_text = ", ".join(p for k, p in PERMISSIONS if k in perms) or "None"
    name = a[2] or a[1] or str(user_id)
    text = (
        f"👤 <b>{name}</b>\n"
        f"ID: <code>{user_id}</code>\n"
        f"Status: {'🟢 Active' if a[3] else '🔴 Disabled'}\n\n"
        f"Permissions: {perm_text}"
    )
    await callback.message.edit_text(text, reply_markup=admin_actions(user_id))
    await callback.answer()

@router.callback_query(F.data == "admin:permissions")
async def permissions_menu(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    admins = await get_admins()
    await callback.message.edit_text(
        "🔐 <b>PERMISSIONS</b>\n\nSelect an admin:",
        reply_markup=admin_list_buttons(admins)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin:perms:"))
async def permissions(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    user_id = int(callback.data.split(":")[2])
    perms = await get_permissions(user_id)
    await callback.message.edit_text(
        f"🔐 <b>PERMISSIONS</b>\n\nAdmin: <code>{user_id}</code>",
        reply_markup=permission_buttons(user_id, perms)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin:toggle:"))
async def toggle_permission(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    _, _, uid, permission = callback.data.split(":")
    user_id = int(uid)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT enabled FROM admin_permissions WHERE user_id=? AND permission=?",
            (user_id, permission)
        )
        row = await cur.fetchone()
        new_value = 0 if row and row[0] else 1
        await db.execute(
            "INSERT INTO admin_permissions(user_id, permission, enabled) VALUES(?,?,?) "
            "ON CONFLICT(user_id, permission) DO UPDATE SET enabled=excluded.enabled",
            (user_id, permission, new_value)
        )
        await db.commit()
    perms = await get_permissions(user_id)
    await callback.message.edit_reply_markup(reply_markup=permission_buttons(user_id, perms))
    await callback.answer("Updated.")

@router.callback_query(F.data.startswith("admin:remove:"))
async def remove_admin(callback: CallbackQuery):
    if not owner(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True); return
    user_id = int(callback.data.split(":")[2])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()
    await callback.message.edit_text(
        "✅ Admin removed.",
        reply_markup=admin_menu()
    )
    await callback.answer()
