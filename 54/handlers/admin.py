from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from datetime import datetime, timedelta

from utils.time_parser import parse_time
from utils.i18n import i18n
from database.manager import get_db

router = Router()

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!kick")
async def kick_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin", "helper"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                target_user = entity.user
            # Simple mention parsing if needed, but text_mention is reliable

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
                        # We need a User object or at least ID. 
                        # aiogram methods usually take ID.
                        # Mocking a simple object or just passing ID where needed.
                        # But for full_name we might need to fetch info? 
                        # We can just use username or "User" if name unknown.
                        from aiogram.types import User
                        target_user = User(id=user_id, is_bot=False, first_name=username_query)
        
        # If still not found and arguments exist, maybe user ID? 
        # But commonly just username/reply.
        pass # If we fail here, target_user is None
    
    if not target_user:
        await message.reply(i18n.get(lang_code, "user_not_found"))
        return

    chat_id = message.chat.id
    revoke_msgs = True # Default
    
    async with get_db() as db:
        async with db.execute("SELECT delete_on_kick FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                revoke_msgs = bool(row[0])

    try:
        # Kick implementation: Ban (possibly deleting messages) then Unban
        await message.chat.ban(target_user.id, revoke_messages=revoke_msgs)
        await message.chat.unban(target_user.id)
        await message.reply(i18n.get(lang_code, "kick_issued", name=target_user.full_name))
        
        from utils.logger import log_action
        await log_action(message.bot, message.chat.id, "Kick", f"User: {target_user.full_name} (ID: {target_user.id})\nAdmin: {message.from_user.full_name}")
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!ban")
async def ban_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin", "helper"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    parts = message.text.split()
    time_delta = None
    
    for part in parts:
        parsed = parse_time(part)
        if parsed:
            time_delta = parsed
            break

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_mention":
                target_user = entity.user

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

    until_date = None
    if time_delta:
        until_date = datetime.now() + time_delta

    revoke_msgs = True
    async with get_db() as db:
        async with db.execute("SELECT delete_on_ban FROM chats WHERE chat_id = ?", (message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                revoke_msgs = bool(row[0])

    try:
        await message.chat.ban(target_user.id, until_date=until_date, revoke_messages=revoke_msgs)
        await message.reply(i18n.get(lang_code, "ban_issued", name=target_user.full_name))
        
        from utils.logger import log_action
        await log_action(message.bot, message.chat.id, "Ban", f"User: {target_user.full_name}\nUntil: {until_date}\nAdmin: {message.from_user.full_name}")
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!mute")
async def mute_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin", "helper"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    parts = message.text.split()
    time_delta = None
    for part in parts:
        parsed = parse_time(part)
        if parsed:
            time_delta = parsed
            break

    if not time_delta:
        time_delta = timedelta(hours=1)

    # Minimum check: < 60s -> 60s
    if time_delta < timedelta(seconds=60):
        time_delta = timedelta(seconds=60)

    # Restriction: Max 90 days
    if time_delta > timedelta(days=90):
        time_delta = timedelta(days=90)

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif message.entities:
       for entity in message.entities:
            if entity.type == "text_mention":
                target_user = entity.user

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

    until_date = datetime.now() + time_delta

    try:
        from aiogram.types import ChatPermissions
        await message.chat.restrict(
            target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await message.reply(i18n.get(lang_code, "mute_issued", name=target_user.full_name, time=str(time_delta)))
        
        from utils.logger import log_action
        await log_action(message.bot, message.chat.id, "Mute", f"User: {target_user.full_name}\nTime: {time_delta}\nAdmin: {message.from_user.full_name}")
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!unban")
async def unban_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
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

    try:
        await message.chat.unban(target_user.id)
        await message.reply(i18n.get(lang_code, "unban_success", name=target_user.full_name))
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!unmute")
async def unmute_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin", "helper"]:
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

    try:
        from aiogram.types import ChatPermissions
        await message.chat.restrict(
            target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
        await message.reply(i18n.get(lang_code, "unmute_success", name=target_user.full_name))
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!mdelete")
async def mdelete_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
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

    try:
        # User requested NOT to kick the user.
        # Telegram API does not allow mass deleting messages without Kicking (Ban) & Revoking Messages.
        # Since we cannot kick, we can only delete the message that was replied to (if any).
        
        if message.reply_to_message:
            await message.reply_to_message.delete()
            await message.delete() # Delete command
            # await message.answer(f"Сообщение от {target_user.full_name} удалено.") 
        else:
             await message.reply(i18n.get(lang_code, "mdelete_no_kick_perm"))
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(lambda msg: msg.text and msg.text.split()[0] == "!setadmin")
async def setadmin_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    parts = message.text.split()
    # Usage: !setadmin [user] [level]
    # We need to find the level argument (last one likely) and user
    
    level = None
    target_user = None
    
    # Try to parse level from the last argument
    if len(parts) >= 2 and parts[-1].isdigit():
        level = int(parts[-1])
        # Remove level from text to parse user
        text_without_level = " ".join(parts[:-1])
    else:
        # Maybe reply?
        if len(parts) == 2 and parts[1].isdigit(): # !setadmin 1 (reply)
             level = int(parts[1])
             text_without_level = parts[0]
        else:
             await message.reply(i18n.get(lang_code, "invalid_level"))
             return

    if level not in [0, 1, 2]:
        await message.reply(i18n.get(lang_code, "invalid_level"))
        return

    # Check Hierarchy Permissions
    if level == 2 and user_role != "owner":
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return
    
    if level == 1 and user_role not in ["owner", "head_admin"]:
         await message.reply(i18n.get(lang_code, "permission_denied"))
         return

    # Find User
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif message.entities:
         for entity in message.entities:
            if entity.type == "text_mention":
                target_user = entity.user
                break
    
    if not target_user:
        # Try @username from parts (excluding level if we found it)
        # Re-split text_without_level
        sub_parts = message.text.split()[:-1] if level is not None else message.text.split()
        username_query = None
        for word in sub_parts:
            if word.startswith("@"):
                username_query = word[1:].lower()
                break
        
        if username_query:
            async with get_db() as db:
                async with db.execute("SELECT user_id FROM users WHERE username = ? AND chat_id = ?", (username_query, message.chat.id)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        from aiogram.types import User
                        target_user = User(id=row[0], is_bot=False, first_name=username_query)

    if not target_user:
        await message.reply(i18n.get(lang_code, "user_not_found"))
        return

    # Execute Role Change
    role_map = {0: "user", 1: "helper", 2: "head_admin"}
    new_role = role_map[level]
    
    # Preventing demotion of Owner or Head Admin by lower rank?
    # Middleware checks handle execution permission based on caller's role.
    # But we should check target's current role too.
    
    async with get_db() as db:
        # Check target current role
        target_role = "user"
        async with db.execute("SELECT role FROM users WHERE user_id = ? AND chat_id = ?", (target_user.id, message.chat.id)) as cursor:
             row = await cursor.fetchone()
             if row: target_role = row[0]
        
        # Hierarchy Protection
        if target_role == "owner":
             await message.reply(i18n.get(lang_code, "role_change_owner_fail"))
             return
        
        if target_role == "head_admin" and user_role != "owner":
             await message.reply(i18n.get(lang_code, "role_change_head_fail"))
             return

        # Update
        await db.execute("INSERT OR REPLACE INTO users (user_id, chat_id, role, username) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, chat_id) DO UPDATE SET role=excluded.role", 
                         (target_user.id, message.chat.id, new_role, target_user.first_name)) # Best effort username
        
        # We also need to preserve other stats if we use INSERT OR REPLACE. 
        # Actually better to use UPDATE if exists, else INSERT.
        # But `users` PK is (user_id, chat_id)
        
        # Safer SQL for partial update:
        await db.execute("""
            UPDATE users SET role = ? WHERE user_id = ? AND chat_id = ?
        """, (new_role, target_user.id, message.chat.id))
        
        # If no row updated (user not in DB yet), insert
        async with db.execute("SELECT changes()") as cursor:
             ret = await cursor.fetchone()
             if ret and ret[0] == 0:
                  await db.execute("INSERT INTO users (user_id, chat_id, role) VALUES (?, ?, ?)", (target_user.id, message.chat.id, new_role))

        await db.commit()

    if level == 0:
        await message.reply(i18n.get(lang_code, "admin_demoted", name=target_user.full_name))
    else:
        role_name_key = f"role_{new_role}"
        role_text = i18n.get(lang_code, role_name_key)
        await message.reply(i18n.get(lang_code, "admin_promoted", name=target_user.full_name, role=role_text))
