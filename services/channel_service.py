async def verify_channel(bot, chat_ref):
    chat=await bot.get_chat(chat_ref)
    me=await bot.get_me()
    member=await bot.get_chat_member(chat.id, me.id)
    if member.status not in {"administrator","creator"}:
        raise ValueError("Bot is not an administrator in this channel.")
    if member.status == "administrator" and not getattr(member, "can_invite_users", False):
        raise ValueError("Bot needs permission to invite users / manage join requests.")
    return chat, member
