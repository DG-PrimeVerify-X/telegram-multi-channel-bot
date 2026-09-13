async def track_message_user(db, message):
    if message.from_user:
        await db.upsert_user(message.from_user)
