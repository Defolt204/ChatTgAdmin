from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from database.manager import get_db

class StatsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not event.from_user or event.from_user.is_bot:
            return await handler(event, data)

        user_id = event.from_user.id
        chat_id = event.chat.id

        username = event.from_user.username
        if username:
            username = username.lower()

        async with get_db() as db:
            await db.execute("""
                INSERT INTO users (user_id, chat_id, username, message_count) 
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, chat_id) DO UPDATE SET 
                    message_count = message_count + 1,
                    username = COALESCE(excluded.username, users.username)
            """, (user_id, chat_id, username))
            await db.commit()

        return await handler(event, data)
