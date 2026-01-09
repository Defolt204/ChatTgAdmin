from aiogram import Router, F
import aiosqlite
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.manager import get_db
from utils.i18n import i18n

router = Router()

class SettingsStates(StatesGroup):
    waiting_for_limit = State()
    waiting_for_ban_duration = State()
    waiting_for_censor_time = State()

@router.message(F.text.in_({"!settings", "!setting"}))
async def settings_handler(message: Message, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        return

    async with get_db() as db:
        db.row_factory = aiosqlite.Row # Enable name access
        async with db.execute("SELECT * FROM chats WHERE chat_id = ?", (message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute("INSERT INTO chats (chat_id) VALUES (?)", (message.chat.id,))
                await db.commit()
                async with db.execute("SELECT * FROM chats WHERE chat_id = ?", (message.chat.id,)) as cursor:
                    row = await cursor.fetchone()
            
            await message.reply(f"⚙️ <b>{i18n.get(lang_code, 'btn_punishment').split(':')[0]}:</b>", reply_markup=get_settings_keyboard(row, lang_code))

def get_settings_keyboard(row, lang_code):
    # row is aiosqlite.Row (supports index and key access)
    # Safe fallback if not Row (e.g. legacy calls) but we updated handlers.
    
    # Extract values safely
    try:
        limit = row["warn_limit"]
        punishment = row["warn_punishment"]
        del_ban = row["delete_on_ban"]
        del_kick = row["delete_on_kick"]
        del_mute = row["delete_on_mute"]
        # can_setname = row["users_can_setname"] # Not used in main menu? Added in previous versions?
        chat_lang = row["language"]
    except (TypeError, IndexError, KeyError):
        # Fallback to indices if something breaks or old code
        # 0:chat_id, 1:lang, 2:limit, 3:punish, 4:del_ban, 5:del_kick, 6:del_mute
        chat_lang = row[1]
        limit = row[2]
        punishment = row[3]
        del_ban = row[4]
        del_kick = row[5]
        del_mute = row[6]

    # Format punishment display
    punish_display = punishment
    if punishment == "kick":
        punish_display = i18n.get(lang_code, "val_kick")
    elif punishment == "ban":
        punish_display = i18n.get(lang_code, "val_ban")
    elif punishment.startswith("ban_"):
        try:
            days = int(punishment.split("_")[1]) // 86400
            punish_display = i18n.get(lang_code, "val_ban_temp", days=days)
        except:
             punish_display = punishment

    keyboard = [
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_lang", language_name=chat_lang.upper()), callback_data="set_language")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_limit", limit=limit), callback_data="set_warn_limit")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_punishment", punishment=punish_display), callback_data="set_punishment")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_censor"), callback_data="set_censor")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_del_ban", status='✅' if del_ban else '❌'), callback_data="toggle_del_ban")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_del_kick", status='✅' if del_kick else '❌'), callback_data="toggle_del_kick")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_del_mute", status='✅' if del_mute else '❌'), callback_data="toggle_del_mute")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_close"), callback_data="close_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- Language ---
@router.callback_query(F.data == "set_language")
async def set_language_menu(callback: CallbackQuery, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await callback.answer(i18n.get(lang_code, "permission_denied"), show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
         InlineKeyboardButton(text="Українська", callback_data="lang_ua")],
        [InlineKeyboardButton(text="Deutsch", callback_data="lang_de"),
         InlineKeyboardButton(text="English", callback_data="lang_en")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_back"), callback_data="back_to_settings")]
    ]
    await callback.message.edit_text(i18n.get(lang_code, "btn_lang", language_name="...").split(":")[0] + ":", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery, user_role: str, state: FSMContext):
    if user_role not in ["owner", "head_admin"]:
        await callback.answer("Access denied", show_alert=True)
        return

    new_lang = callback.data.split("_")[1]
    
    async with get_db() as db:
        await db.execute("UPDATE chats SET language = ? WHERE chat_id = ?", (new_lang, callback.message.chat.id))
        await db.commit()
        
        async with db.execute("SELECT * FROM chats WHERE chat_id = ?", (callback.message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            # Use new_lang to display menu
            await callback.message.edit_text("⚙️", reply_markup=get_settings_keyboard(row, new_lang))
    
    await callback.answer(f"Language set to {new_lang.upper()}")

# --- Warn Limit ---
@router.callback_query(F.data == "set_warn_limit")
async def set_warn_limit_prompt(callback: CallbackQuery, user_role: str, lang_code: str, state: FSMContext):
    if user_role not in ["owner", "head_admin"]:
        await callback.answer(i18n.get(lang_code, "permission_denied"), show_alert=True)
        return
    
    await state.set_state(SettingsStates.waiting_for_limit)
    await callback.message.answer(i18n.get(lang_code, "msg_enter_limit"))
    await callback.answer()

@router.message(SettingsStates.waiting_for_limit)
async def limit_input(message: Message, state: FSMContext, lang_code: str):
    if not message.text.isdigit():
        await message.reply(i18n.get(lang_code, "msg_invalid_input"))
        return
    
    limit = int(message.text)
    async with get_db() as db:
        await db.execute("UPDATE chats SET warn_limit = ? WHERE chat_id = ?", (limit, message.chat.id))
        await db.commit()
    
    await message.reply(i18n.get(lang_code, "msg_limit_updated", limit=limit))
    await state.clear()

# --- Punishment ---
@router.callback_query(F.data == "set_punishment")
async def set_punishment_menu(callback: CallbackQuery, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await callback.answer(i18n.get(lang_code, "permission_denied"), show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_kick"), callback_data="punish_kick")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_ban"), callback_data="punish_ban_menu")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_back"), callback_data="back_to_settings")]
    ]
    await callback.message.edit_text(i18n.get(lang_code, "msg_select_punishment"), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data == "punish_kick")
async def set_punish_kick(callback: CallbackQuery, lang_code: str):
    async with get_db() as db:
        await db.execute("UPDATE chats SET warn_punishment = 'kick' WHERE chat_id = ?", (callback.message.chat.id,))
        await db.commit()
        await callback_to_main(callback, db, lang_code)

@router.callback_query(F.data == "punish_ban_menu")
async def punish_ban_menu(callback: CallbackQuery, lang_code: str):
    keyboard = [
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_perm"), callback_data="punish_ban_perm")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_temp"), callback_data="punish_ban_temp")],
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_back"), callback_data="set_punishment")]
    ]
    await callback.message.edit_text(i18n.get(lang_code, "msg_select_ban_type"), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data == "punish_ban_perm")
async def set_punish_ban_perm(callback: CallbackQuery, lang_code: str):
    async with get_db() as db:
        await db.execute("UPDATE chats SET warn_punishment = 'ban' WHERE chat_id = ?", (callback.message.chat.id,))
        await db.commit()
        await callback_to_main(callback, db, lang_code)

@router.callback_query(F.data == "punish_ban_temp")
async def set_punish_ban_temp_prompt(callback: CallbackQuery, state: FSMContext, lang_code: str):
    await state.set_state(SettingsStates.waiting_for_ban_duration)
    await callback.message.answer(i18n.get(lang_code, "msg_enter_days"))
    await callback.answer()

@router.message(SettingsStates.waiting_for_ban_duration)
async def duration_input(message: Message, state: FSMContext, lang_code: str):
    if not message.text.isdigit():
        await message.reply(i18n.get(lang_code, "msg_invalid_input"))
        return
    
    days = int(message.text)
    seconds = days * 86400
    punishment_val = f"ban_{seconds}"
    
    async with get_db() as db:
        await db.execute("UPDATE chats SET warn_punishment = ? WHERE chat_id = ?", (punishment_val, message.chat.id))
        await db.commit()
        
    await message.reply(i18n.get(lang_code, "msg_punish_updated", punishment=f"Ban {days} days"))
    await state.clear()

# --- Common ---
@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery, lang_code: str):
    async with get_db() as db:
        await callback_to_main(callback, db, lang_code)

@router.callback_query(F.data.startswith("toggle_"))
async def toggle_setting(callback: CallbackQuery, user_role: str, lang_code: str):
    if user_role not in ["owner", "head_admin"]:
        await callback.answer(i18n.get(lang_code, "permission_denied"), show_alert=True)
        return
    field_map = {"toggle_del_ban": "delete_on_ban", "toggle_del_kick": "delete_on_kick", "toggle_del_mute": "delete_on_mute", "toggle_setname": "users_can_setname"}
    field = field_map.get(callback.data)
    if not field: return

    async with get_db() as db:
        await db.execute(f"UPDATE chats SET {field} = 1 - {field} WHERE chat_id = ?", (callback.message.chat.id,))
        await db.commit()
        await callback_to_main(callback, db, lang_code)
    await callback.answer()

@router.callback_query(F.data == "close_settings")
async def close_settings(callback: CallbackQuery):
    await callback.message.delete()

async def callback_to_main(callback, db, lang_code):
    db.row_factory = aiosqlite.Row
    async with db.execute("SELECT * FROM chats WHERE chat_id = ?", (callback.message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            await callback.message.edit_text("⚙️", reply_markup=get_settings_keyboard(row, lang_code))

# --- Censor Settings ---
@router.callback_query(F.data == "set_censor")
async def censor_settings_menu(callback: CallbackQuery, lang_code: str):
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT censor_punishment, censor_punish_duration FROM chats WHERE chat_id = ?", (callback.message.chat.id,)) as cursor:
            row = await cursor.fetchone()
            if not row: return # Should not happen
            
            punishment = row["censor_punishment"]
            duration = row["censor_punish_duration"]
            
    # Format
    p_display = punishment
    if punishment == "mute": p_display = i18n.get(lang_code, "val_mute")
    elif punishment == "warn": p_display = i18n.get(lang_code, "val_warn")
    elif punishment == "none": p_display = i18n.get(lang_code, "val_none")
    
    time_display = f"{duration // 60} min"
    
    keyboard = [
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_censor_punish", punishment=p_display), callback_data="set_censor_punish")],
        # Show mute time only if punishment is mute
        # But user wants to be able to change it? Yes.
        ([InlineKeyboardButton(text=i18n.get(lang_code, "btn_censor_time", time=time_display), callback_data="set_censor_time")] if punishment == "mute" else []),
        [InlineKeyboardButton(text=i18n.get(lang_code, "btn_back"), callback_data="back_to_settings")]
    ]
    # Flatten checks
    final_kb = [k for k in keyboard if k]
    
    await callback.message.edit_text(i18n.get(lang_code, "msg_censor_menu"), reply_markup=InlineKeyboardMarkup(inline_keyboard=final_kb))

@router.callback_query(F.data == "set_censor_punish")
async def toggle_censor_punish(callback: CallbackQuery, lang_code: str):
    # Toggle Mute -> Warn -> None -> Mute
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT censor_punishment FROM chats WHERE chat_id = ?", (callback.message.chat.id,)) as cursor:
             row = await cursor.fetchone()
             
        current = row["censor_punishment"]
        next_map = {"mute": "warn", "warn": "none", "none": "mute"}
        new_val = next_map.get(current, "mute")
        
        await db.execute("UPDATE chats SET censor_punishment = ? WHERE chat_id = ?", (new_val, callback.message.chat.id))
        await db.commit()
        
    await censor_settings_menu(callback, lang_code)

@router.callback_query(F.data == "set_censor_time")
async def set_censor_time_prompt(callback: CallbackQuery, state: FSMContext, lang_code: str):
    await state.set_state(SettingsStates.waiting_for_censor_time)
    await callback.message.answer(i18n.get(lang_code, "msg_censor_time"))
    await callback.answer()

@router.message(SettingsStates.waiting_for_censor_time)
async def censor_time_input(message: Message, state: FSMContext, lang_code: str):
    if not message.text.isdigit():
        await message.reply(i18n.get(lang_code, "msg_invalid_input"))
        return
    
    minutes = int(message.text)
    seconds = minutes * 60
    # Min 1 min
    if seconds < 60: seconds = 60
    
    async with get_db() as db:
        await db.execute("UPDATE chats SET censor_punish_duration = ? WHERE chat_id = ?", (seconds, message.chat.id))
        await db.commit()
        
    await message.reply(i18n.get(lang_code, "msg_limit_updated", limit=f"{minutes} min")) # Reuse or new msg? "Time updated"
    # User might want specific msg. Reusing limit updated is okay-ish but "Time updated" is better.
    # But I didn't add "msg_time_updated". I will reuse punishment updated? 
    # "Punishment updated to: 10 min mute"
    
    await state.clear()
