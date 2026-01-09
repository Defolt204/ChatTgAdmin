from aiogram import Router, F
from aiogram.types import Message
from database.manager import get_db
from utils.i18n import i18n

router = Router()

@router.message(F.text.startswith("!stat"))
async def stat_handler(message: Message, user_role: str, lang_code: str):
    user_id = message.from_user.id
    chat_id = message.chat.id
    target_user = message.from_user

    # Admin check for viewing others
    if user_role in ["owner", "head_admin", "helper"]:
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        elif len(message.entities or []) > 0:
             # Check for mention
             for entity in message.entities:
                if entity.type == "text_mention":
                    target_user = entity.user
                    break
             # Also check simple @mentions via DB lookup if needed, 
             # but keeping it simple for now as text_mention is robust for clicks.
             # If text contains @username, we can try lookup (reuse logic from admin.py if we want perfection)
             
             if target_user.id == message.from_user.id: 
                 # If no entity found or it is self, check for @username argument
                 parts = message.text.split()
                 username_query = None
                 for part in parts:
                     if part.startswith("@"):
                         username_query = part[1:].lower()
                         break
                 
                 if username_query:
                     async with get_db() as db:
                         async with db.execute("SELECT user_id, username FROM users WHERE username = ? AND chat_id = ?", (username_query, chat_id)) as cursor:
                             row = await cursor.fetchone()
                             if row:
                                 from aiogram.types import User
                                 # Mock user for display
                                 target_user = User(id=row[0], is_bot=False, first_name=row[1] or username_query)

    async with get_db() as db:
        async with db.execute(
            "SELECT message_count, warns, joined_date, role FROM users WHERE user_id = ? AND chat_id = ?",
            (target_user.id, chat_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                msgs, warns, joined_str, db_role = row
                
                # Calculate days
                from datetime import datetime
                days_in_chat = 0
                joined_clean = joined_str
                try:
                    # SQLite default format: YYYY-MM-DD HH:MM:SS
                    # It might be in different format depending on how it was inserted.
                    # Assuming ISO-like
                    joined_dt = datetime.fromisoformat(joined_str)
                    days_in_chat = (datetime.now() - joined_dt).days
                    joined_clean = joined_dt.strftime("%d.%m.%Y")
                except Exception:
                    # Fallback if parsing fails
                    pass

                # Localize Role
                role_key = f"role_{db_role}"
                role_name = i18n.get(lang_code, role_key)
                if role_name == role_key: role_name = db_role.title()

                await message.reply(i18n.get(
                    lang_code, "stat_text",
                    name=target_user.full_name,
                    date=joined_clean,
                    days=days_in_chat,
                    msgs=msgs,
                    warns=warns,
                    role=role_name
                ))
            else:
                await message.reply(i18n.get(lang_code, "user_not_found"))


        
