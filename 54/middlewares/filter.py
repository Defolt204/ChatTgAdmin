from aiogram import BaseMiddleware
from aiogram.types import Message
from database.manager import get_db
from utils.logger import log_action
from utils.i18n import i18n
from utils.i18n import i18n
from datetime import datetime, timedelta
from aiogram.types import ChatPermissions
import re

class FilterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)
            
        user_role = data.get("user_role", "user")
        lang_code = data.get("lang_code", "ru")
        
        # Admins are exempt
        if user_role in ["owner", "head_admin", "helper"]:
            return await handler(event, data)
            
        chat_id = event.chat.id
        text = event.text.lower()
        
        # Fetch settings
        censor_enabled = False
        antilink_enabled = False
        antilink_warn = False
        
        async with get_db() as db:
            async with db.execute("SELECT censor_enabled, antilink_enabled, antilink_warn, censor_punishment, censor_punish_duration, warn_limit, warn_punishment FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    censor_enabled = bool(row[0])
                    antilink_enabled = bool(row[1])
                    antilink_warn = bool(row[2])
                    censor_punishment = row[3] or "mute"
                    censor_duration = row[4] or 180
                    warn_limit = row[5] or 3
                    warn_punishment = row[6] or "ban"
                    
            # Censor Check
            if censor_enabled:
                async with db.execute("SELECT word FROM banned_words WHERE chat_id = ?", (chat_id,)) as cursor:
                    rows = await cursor.fetchall()
                    banned_words = [r[0] for r in rows]
                    
                for word in banned_words:
                    # Use regex for whole matches to avoid false positives (e.g. 'ass' in 'class')
                    # Escape word to handle special characters safe
                    if re.search(r'\b' + re.escape(word) + r'\b', text):
                        await event.delete()
                        await event.answer(i18n.get(lang_code, "censor_warn", name=event.from_user.full_name))
                        
                        if censor_punishment == "mute":
                             until_date = datetime.now() + timedelta(seconds=censor_duration)
                             try:
                                 await event.chat.restrict(
                                     event.from_user.id,
                                     permissions=ChatPermissions(can_send_messages=False),
                                     until_date=until_date
                                 )
                                 await event.answer(i18n.get(lang_code, "censor_mute", time=f"{censor_duration//60} min"))
                             except Exception as e:
                                 await event.answer(f"Failed to mute: {e}") # Debugging feedback
                                 log_action(event.bot, chat_id, "Censor Error", f"Failed to mute {event.from_user.id}: {e}")

                        elif censor_punishment == "warn":
                             current_warns = 0
                             async with db.execute("SELECT warns FROM users WHERE user_id = ? AND chat_id = ?", (event.from_user.id, chat_id)) as cur:
                                  r = await cur.fetchone()
                                  if r: current_warns = r[0]
                             
                             current_warns += 1
                             
                             if current_warns >= warn_limit:
                                 # Punishment Escalation
                                 punish_msg = ""
                                 try:
                                     if warn_punishment == "ban":
                                         await event.chat.ban(event.from_user.id)
                                         punish_msg = i18n.get(lang_code, "val_ban")
                                     elif warn_punishment == "kick":
                                         await event.chat.unban(event.from_user.id)
                                         punish_msg = i18n.get(lang_code, "val_kick")
                                     elif warn_punishment.startswith("ban_"):
                                         seconds = int(warn_punishment.split("_")[1])
                                         until = datetime.now() + timedelta(seconds=seconds)
                                         await event.chat.ban(event.from_user.id, until_date=until)
                                         punish_msg = i18n.get(lang_code, "val_ban_temp", days=seconds//86400)
                                     
                                     await db.execute("UPDATE users SET warns = 0 WHERE user_id = ? AND chat_id = ?", (event.from_user.id, chat_id))
                                     await event.answer(i18n.get(lang_code, "msg_punish_updated", punishment=punish_msg))
                                     
                                     await log_action(event.bot, chat_id, "Punishment", f"User {event.from_user.id} reached warn limit via Censor. Punishment: {warn_punishment}")
                                 except Exception as e:
                                     await event.answer(f"Error punishing: {e}")
                                     log_action(event.bot, chat_id, "Punish Error", f"Failed to punish {event.from_user.id}: {e}")
                             else:
                                 await db.execute("UPDATE users SET warns = ? WHERE user_id = ? AND chat_id = ?", (current_warns, event.from_user.id, chat_id))
                                 await event.answer(i18n.get(lang_code, "warn_issued", name=event.from_user.full_name, count=current_warns, limit=warn_limit))
                             
                             await db.commit()

                             
                        await log_action(event.bot, chat_id, "Censor", f"Message deleted. Word: {word}. Punishment: {censor_punishment}")
                        return # Stop processing
            
            # Anti-Link Check
            if antilink_enabled:
                # Regex for URLs and Telegram links
                url_pattern = r"(https?://\S+|www\.\S+|t\.me/\S+|@\w+)"
                if re.search(url_pattern, text):
                     await event.delete()
                     await event.answer(i18n.get(lang_code, "antilink_warn", name=event.from_user.full_name))
                     
                     if antilink_warn:
                        current_warns = 0
                        async with db.execute("SELECT warns FROM users WHERE user_id = ? AND chat_id = ?", (event.from_user.id, chat_id)) as cur:
                             r = await cur.fetchone()
                             if r: current_warns = r[0]
                        current_warns += 1
                        await db.execute("UPDATE users SET warns = ? WHERE user_id = ? AND chat_id = ?", (current_warns, event.from_user.id, chat_id))
                        await db.commit()
                        
                     await log_action(event.bot, chat_id, "Anti-Link", f"Link deleted from {event.from_user.full_name}.")
                     return

        return await handler(event, data)
