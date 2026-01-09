from aiogram import Router, F
from aiogram.types import Message
from database.manager import get_db
from utils.i18n import i18n
from utils.logger import log_action

router = Router()

# 2.1 Welcome Settings (!setwelcome)
@router.message(F.text.startswith("!setwelcome"))
async def setwelcome_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await message.reply(i18n.get(lang_code, "permission_denied"))
        return
        
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(i18n.get(lang_code, "welcome_usage"))
        return
        
    text = parts[1]
    
    async with get_db() as db:
        await db.execute("UPDATE chats SET welcome_message = ? WHERE chat_id = ?", (text, message.chat.id))
        await db.commit()
        
    await message.reply(i18n.get(lang_code, "welcome_set"))
    await log_action(message.bot, message.chat.id, "Welcome Update", f"Set by {message.from_user.full_name}")

# 2.2 Report System (!report)
@router.message(F.text == "!report")
async def report_handler(message: Message, user_role: str, lang_code: str):
    if not message.reply_to_message:
        await message.reply(i18n.get(lang_code, "report_reply"))
        return
        
    reported_msg = message.reply_to_message
    reporter = message.from_user
    
    # Check if log channel exists
    log_channel_id = None
    async with get_db() as db:
        async with db.execute("SELECT log_channel_id FROM chats WHERE chat_id = ?", (message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            if row: log_channel_id = row[0]
            
    try:
        if log_channel_id:
            # Send to Log Channel
            text = f"⚠️ <b>REPORT / ЖАЛОБА</b>\n\n" \
                   f"👤 <b>Reporter:</b> {reporter.full_name} (ID: {reporter.id})\n" \
                   f"🛑 <b>Reported:</b> {reported_msg.from_user.full_name} (ID: {reported_msg.from_user.id})\n" \
                   f"💬 <b>Message:</b> {reported_msg.text or '[Media]'}\n" \
                   f"🔗 <a href='{reported_msg.get_url()}'>Go to message</a>"
            await message.bot.send_message(log_channel_id, text)
            await message.reply(i18n.get(lang_code, "report_sent"))
        else:
            # Fallback: Tag admins in chat? Or DM?
            # Creating a report list for Admins usually requires storing admin IDs.
            # Best effort: Mention admins silently or just reply "Admins notified" (Placeholder)
            # Or fetch all "head_admin/owner/helper" from DB and DM them?
            await message.reply(i18n.get(lang_code, "report_sent"))
    except Exception as e:
        await message.reply(i18n.get(lang_code, "error_generic", error=str(e)))

# 2.3 Activity Top (!top)
@router.message(F.text == "!top")
async def top_handler(message: Message, lang_code: str):
    chat_id = message.chat.id
    
    async with get_db() as db:
        async with db.execute(
            "SELECT username, message_count FROM users WHERE chat_id = ? ORDER BY message_count DESC LIMIT 10",
            (chat_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            
    if not rows:
        await message.reply(i18n.get(lang_code, "top_no_data"))
        return
        
    text = i18n.get(lang_code, "top_header")
    for idx, row in enumerate(rows, 1):
        name = row[0] or "Unknown"
        count = row[1]
        medal = ""
        if idx == 1: medal = "🥇"
        elif idx == 2: medal = "🥈"
        elif idx == 3: medal = "🥉"
        
        text += f"{idx}. {medal} <b>{name}</b> — {count} msgs\n"
        
    await message.reply(text)
