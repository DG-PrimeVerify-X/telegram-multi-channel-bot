from aiogram import Router
from aiogram.types import ChatJoinRequest
from services.content_service import deliver_content

router=Router()

@router.chat_join_request()
async def join_request(event:ChatJoinRequest,bot,db):
    user=event.from_user
    await db.upsert_user(user)
    ch=await db.get_channel(event.chat.id)
    if not ch or not ch["active"]:
        return
    await db.add_channel_user(event.chat.id,user.id,"join_request")
    if ch["auto_accept"]:
        try:
            await event.approve()
            await db.add_channel_user(event.chat.id,user.id,"joined")
        except Exception as e:
            await db.log(user.id,"join_approve_error",f"{event.chat.id}: {e}")
            return
    if ch["auto_dm"]:
        sent=await deliver_content(bot,db,event.chat.id,user.id)
        await db.log(user.id,"auto_dm",f"channel={event.chat.id}, sent={sent}")
