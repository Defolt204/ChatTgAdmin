from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, Message
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION
from database.manager import get_db
import asyncio

router = Router()

@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated):
    chat_id = event.chat.id
    new_member = event.new_chat_member.user
    
    # Add to DB immediately
    async with get_db() as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, chat_id, role, username) VALUES (?, ?, 'user', ?)",
            (new_member.id, chat_id, new_member.full_name) # Using full name as fallback for username
        )
        await db.commit()
    
        # Check for welcome message
        welcome_text = None
        async with db.execute("SELECT welcome_message FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row: welcome_text = row[0]
            
    if welcome_text:
        # Replace placeholder
        final_text = welcome_text.replace("{username}", new_member.full_name)
        
        try:
            msg = await event.bot.send_message(chat_id, final_text)
            # Auto-delete after 60s
            await asyncio.sleep(60)
            await msg.delete()
        except Exception as e:
            print(f"Welcome message error: {e}")
