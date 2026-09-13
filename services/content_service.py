async def deliver_content(bot, db, chat_id, user_id):
    items=await db.get_channel_content(chat_id)
    sent=0
    for item in items:
        try:
            await bot.copy_message(user_id, item["source_chat_id"], item["source_message_id"])
            sent += 1
        except Exception:
            pass
    return sent
