import asyncio
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest

async def copy_broadcast(bot, db, owner_id, source_chat_id, source_message_id, targets, label="broadcast"):
    sent=failed=0
    for user_id in targets:
        try:
            await bot.copy_message(chat_id=user_id, from_chat_id=source_chat_id, message_id=source_message_id)
            sent += 1
            await asyncio.sleep(0.05)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=source_chat_id, message_id=source_message_id)
                sent += 1
            except Exception:
                failed += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1
    await db.log(owner_id, label, f"sent={sent}, failed={failed}")
    return sent, failed
