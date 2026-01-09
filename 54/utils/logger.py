from database.manager import get_db
from aiogram import Bot

async def log_action(bot: Bot, chat_id: int, action: str, details: str):
    """
    Logs an action to the configured log channel for the chat.
    """
    log_channel_id = None
    
    async with get_db() as db:
        async with db.execute("SELECT log_channel_id FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                log_channel_id = row[0]
                
    if log_channel_id:
        try:
            # Format the log message
            text = f"📝 <b>LOG REPORT</b>\n\n" \
                   f"📌 <b>Action:</b> {action}\n" \
                   f"ℹ️ <b>Details:</b> {details}"
            
            await bot.send_message(log_channel_id, text)
        except Exception as e:
            print(f"Failed to send log to {log_channel_id}: {e}")
