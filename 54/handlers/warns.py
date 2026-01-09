from aiogram import Router, F
from aiogram.types import Message
from database.manager import get_db
from utils.i18n import i18n
from datetime import datetime, timedelta

router = Router()

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!warn")
async def warn_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin", "moderator"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    
    if not target_user:
        # Try to find by username in DB
        username_query = None
        for word in message.text.split():
            if word.startswith("@"):
                username_query = word[1:].lower()
                break
        
        if username_query:
            async with get_db() as db:
                async with db.execute("SELECT user_id FROM users WHERE username = ? AND chat_id = ?", (username_query, message.chat.id)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        user_id = row[0]
                        from aiogram.types import User
                        target_user = User(id=user_id, is_bot=False, first_name=username_query)

    if not target_user:
        await message.reply(i18n.get(lang_code, "user_not_found"))
        return

    chat_id = message.chat.id
    
    async with get_db() as db:
        # Get chat settings for warn limit and punishment
        async with db.execute("SELECT warn_limit, warn_punishment FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
            settings = await cursor.fetchone()
            if not settings:
                limit, punishment = 3, "ban" # Default
            else:
                limit, punishment = settings

        # Increment warns
        await db.execute("""
            INSERT INTO users (user_id, chat_id, warns) 
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET warns = warns + 1
        """, (target_user.id, chat_id))
        
        async with db.execute("SELECT warns FROM users WHERE user_id = ? AND chat_id = ?", (target_user.id, chat_id)) as cursor:
            row = await cursor.fetchone()
            current_warns = row[0]
            
        await db.commit()

        if current_warns >= limit:
            # Execute punishment
            try:
                if punishment == "ban":
                     await message.chat.ban(target_user.id)
                     punish_name = i18n.get(lang_code, "val_ban")
                elif punishment.startswith("ban_"):
                    # Temporary ban
                    try:
                        seconds = int(punishment.split("_")[1])
                        until_date = datetime.now() + timedelta(seconds=seconds)
                        await message.chat.ban(target_user.id, until_date=until_date)
                        days = seconds // 86400
                        punish_name = i18n.get(lang_code, "val_ban_temp", days=days)
                    except:
                         # Fallback to perm ban if error
                         await message.chat.ban(target_user.id)
                         punish_name = i18n.get(lang_code, "val_ban")
                elif punishment == "kick":
                    await message.chat.unban(target_user.id)
                    punish_name = i18n.get(lang_code, "val_kick")
                elif punishment == "mute":
                    from aiogram.types import ChatPermissions
                    await message.chat.restrict(target_user.id, permissions=ChatPermissions(can_send_messages=False))
                    punish_name = "Mute" # Mute setting not fully added to advanced menu yet, keeping legacy support
                
                await message.reply(i18n.get(lang_code, "msg_punish_updated", punishment=punish_name))
                # Reset warns after punishment
                await db.execute("UPDATE users SET warns = 0 WHERE user_id = ? AND chat_id = ?", (target_user.id, chat_id))
                await db.commit()
            except Exception as e:
                await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))
        else:
            await message.reply(i18n.get(lang_code, "warn_issued", name=target_user.full_name, count=current_warns, limit=limit))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!unwarn")
async def unwarn_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin", "moderator"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        
    if not target_user:
        await message.reply(i18n.get(lang_code, "user_not_found"))
        return

    async with get_db() as db:
        await db.execute("UPDATE users SET warns = MAX(0, warns - 1) WHERE user_id = ? AND chat_id = ?", (target_user.id, message.chat.id))
        await db.commit()
        await message.reply(i18n.get(lang_code, "unwarn_success", name=target_user.full_name))
