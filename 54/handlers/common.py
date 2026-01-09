from aiogram import Router, F
from aiogram.types import Message
from utils.i18n import i18n
from database.manager import get_db

router = Router()

@router.message(F.text == "!start")
async def start_handler(message: Message, lang_code: str):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    async with get_db() as db:
        async with db.execute("SELECT owner_id FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            
            if not row or row[0] is None:
                # Set the first user as owner
                await db.execute("""
                    INSERT INTO chats (chat_id, owner_id) 
                    VALUES (?, ?)
                    ON CONFLICT(chat_id) DO UPDATE SET owner_id = ?
                """, (chat_id, user_id, user_id))
                
                # Also update their role in the users table
                await db.execute("""
                    INSERT INTO users (user_id, chat_id, role)
                    VALUES (?, ?, 'owner')
                    ON CONFLICT(user_id, chat_id) DO UPDATE SET role = 'owner'
                """, (user_id, chat_id))
                
                await db.commit()
                # Ideally utilize lang_code here too
                await message.reply(i18n.get(lang_code, "start_owner_success"))
            else:
                await message.reply(i18n.get(lang_code, "start_owner_fail"))

@router.message(F.text == "!help")
async def help_handler(message: Message, user_role: str, lang_code: str):
    help_key = "help_text"
    if user_role == "owner":
        help_key = "help_owner"
    elif user_role == "head_admin":
        help_key = "help_head_admin"
    elif user_role == "helper":
        help_key = "help_helper"
    else:
        # Default user 
        help_key = "help_user" # If exists, or just help_text
        
    # Retrieve localized role name
    role_key = f"role_{user_role}"
    role_name = i18n.get(lang_code, role_key)
    # If role key missing, fallback to title case
    if role_name == role_key:
        role_name = user_role.replace("_", " ").title()

    text = i18n.get(lang_code, help_key, name=message.from_user.full_name, role=role_name)
    # If key missing/fallback, maybe show general
    if text == help_key: 
        text = i18n.get(lang_code, "help_text")
        
    await message.reply(text)

@router.message(F.text == "!ahelp")
async def ahelp_handler(message: Message, lang_code: str):
    text = i18n.get(lang_code, "ahelp_text")
    await message.reply(text)

@router.message(F.text.startswith("!"))
async def unknown_command(message: Message, lang_code: str):
    # Only if it wasn't caught by other routers
    # Need to handle case where lang_code might be missing if middleware fails?
    # But middleware is global.
    await message.reply(i18n.get(lang_code, "command_not_found"))
