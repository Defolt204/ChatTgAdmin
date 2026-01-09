from typing import Any, Callable, Dict, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import config
from database.manager import get_db

class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        if not user:
             return await handler(event, data)

        user_id = user.id
        
        chat = None
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat
            
        if not chat:
            return await handler(event, data)
            
        chat_id = chat.id
        
        # Default values
        lang_code = "ru"
        
        async with get_db() as db:
            # Fetch chat settings (limit to owner_id and language for now)
            async with db.execute("SELECT owner_id, language FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
                chat_row = await cursor.fetchone()
                chat_owner_id = None
                if chat_row:
                    chat_owner_id = chat_row[0]
                    if chat_row[1]:
                        lang_code = chat_row[1]
            
            data["lang_code"] = lang_code
            
            # Developer/Owner check
            if user_id == config.OWNER_ID:
                data["user_role"] = "owner"
                return await handler(event, data)
                
            # Chat Owner check
            if chat_owner_id == user_id:
                data["user_role"] = "owner"
                return await handler(event, data)

            # DB Role check
            async with db.execute(
                "SELECT role FROM users WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    data["user_role"] = row[0]
                else:
                    # Check Telegram admins if not in DB
                    admins = await event.bot.get_chat_administrators(chat_id)
                    is_admin = any(admin.user.id == user_id for admin in admins)
                    
                    role = "user"
                    if is_admin:
                        try:
                            admin_member = next(a for a in admins if a.user.id == user_id)
                            if admin_member.status == "creator":
                                role = "owner"
                            else:
                                role = "helper"
                        except StopIteration:
                            role = "user"

                    # Auto-insert into DB
                    await db.execute(
                        "INSERT OR IGNORE INTO users (user_id, chat_id, role) VALUES (?, ?, ?)",
                        (user_id, chat_id, role)
                    )
                    await db.commit()
                    data["user_role"] = role

        return await handler(event, data)
