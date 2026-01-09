from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.manager import get_db
from utils.i18n import i18n
from utils.logger import log_action

router = Router()

# 1.1 Lockdown (!lock / !unlock)
@router.message(F.text == "!lock")
async def lock_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    from aiogram.types import ChatPermissions
    
    # permissions=ChatPermissions(can_send_messages=False) makes it read-only for default role
    try:
        await message.chat.set_permissions(ChatPermissions(can_send_messages=False))
        
        async with get_db() as db:
            await db.execute("UPDATE chats SET lockdown_enabled = 1 WHERE chat_id = ?", (message.chat.id,))
            await db.commit()
            
        await message.reply(i18n.get(lang_code, "lock_enabled"))
        await log_action(message.bot, message.chat.id, "Lockdown", f"Enabled by {message.from_user.full_name}")
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

@router.message(F.text == "!unlock")
async def unlock_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return
        
    from aiogram.types import ChatPermissions
    
    try:
        # Default permissions usually enable messages etc.
        await message.chat.set_permissions(ChatPermissions(
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
        ))

        async with get_db() as db:
            await db.execute("UPDATE chats SET lockdown_enabled = 0 WHERE chat_id = ?", (message.chat.id,))
            await db.commit()
            
        await message.reply(i18n.get(lang_code, "unlock_enabled"))
        await log_action(message.bot, message.chat.id, "Unlock", f"Disabled by {message.from_user.full_name}")
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

# 1.2 Censor (!banword, !unbanword, !wordlist)
@router.message(F.text.startswith("!banword"))
async def banword_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return
        
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(i18n.get(lang_code, "banword_usage"))
        return
        
    word = parts[1].lower().strip()
    if not word:
        await message.reply(i18n.get(lang_code, "banword_usage"))
        return

    async with get_db() as db:
        async with db.execute("SELECT 1 FROM banned_words WHERE chat_id = ? AND word = ?", (message.chat.id, word)) as cursor:
            if await cursor.fetchone():
               await message.reply(i18n.get(lang_code, "banword_exists", word=word))
               return

        await db.execute("INSERT OR IGNORE INTO banned_words (chat_id, word) VALUES (?, ?)", (message.chat.id, word))
        await db.commit()
        await db.execute("UPDATE chats SET censor_enabled = 1 WHERE chat_id = ?", (message.chat.id,))
        await db.commit()
        
    await message.reply(i18n.get(lang_code, "banword_added", word=word))
    await log_action(message.bot, message.chat.id, "Censor Update", f"Word '{word}' added by {message.from_user.full_name}")

@router.message(F.text.startswith(("!unbanword", "!rmword")))
async def unbanword_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(i18n.get(lang_code, "banword_usage"))
        return
        
    word = parts[1].lower()
    
    async with get_db() as db:
        await db.execute("DELETE FROM banned_words WHERE chat_id = ? AND word = ?", (message.chat.id, word))
        await db.commit()
        
    await message.reply(i18n.get(lang_code, "banword_removed", word=word))
    await log_action(message.bot, message.chat.id, "Censor Update", f"Word '{word}' removed by {message.from_user.full_name}")

@router.message(F.text.in_({"!wordlist", "!banlist"}))
async def wordlist_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return
        
    async with get_db() as db:
        async with db.execute("SELECT word FROM banned_words WHERE chat_id = ?", (message.chat.id,)) as cursor:
            rows = await cursor.fetchall()
            words = [row[0] for row in rows]
            
    if words:
        text = i18n.get(lang_code, "banword_list", words=", ".join(words))
    else:
        text = i18n.get(lang_code, "banword_empty")
        
    try:
        await message.bot.send_message(message.from_user.id, text)
        await message.reply(i18n.get(lang_code, "wordlist_sent_pm"))
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))
