import aiosqlite
import os

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table: stores stats, status (warns) and bot-level roles
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                chat_id INTEGER,
                username TEXT,
                message_count INTEGER DEFAULT 0,
                warns INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user',
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, chat_id)
            )
        """)
        
        # Migration: Check if username column exists
        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = await cursor.fetchall()
            # columns is list of (cid, name, type, notnull, dflt_value, pk)
            column_names = [col[1] for col in columns]
            
            if "username" not in column_names:
                print("Migrating database: Adding username column...")
                await db.execute("ALTER TABLE users ADD COLUMN username TEXT")
                await db.commit()
        
        # Chats table: stores chat-specific settings
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                warn_limit INTEGER DEFAULT 3,
                warn_punishment TEXT DEFAULT 'ban',
                delete_on_ban INTEGER DEFAULT 1,
                delete_on_kick INTEGER DEFAULT 1,
                delete_on_mute INTEGER DEFAULT 0,
                users_can_setname INTEGER DEFAULT 1,
                owner_id INTEGER,
                log_channel_id INTEGER,
                welcome_message TEXT,
                antilink_enabled INTEGER DEFAULT 0,
                antilink_warn INTEGER DEFAULT 0,
                censor_enabled INTEGER DEFAULT 0,
                censor_punishment TEXT DEFAULT 'mute',
                censor_punish_duration INTEGER DEFAULT 180,
                lockdown_enabled INTEGER DEFAULT 0
            )
        """)
        
        # Banned Words table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS banned_words (
                chat_id INTEGER,
                word TEXT,
                PRIMARY KEY (chat_id, word)
            )
        """)

        # Migration for chats table (add new columns if missing)
        async with db.execute("PRAGMA table_info(chats)") as cursor:
            columns = await cursor.fetchall()
            max_col_names = [col[1] for col in columns]
            
            new_cols = {
                "log_channel_id": "INTEGER",
                "welcome_message": "TEXT",
                "antilink_enabled": "INTEGER DEFAULT 0",
                "antilink_warn": "INTEGER DEFAULT 0",
                "censor_enabled": "INTEGER DEFAULT 0",
                "censor_enabled": "INTEGER DEFAULT 0",
                "censor_punishment": "TEXT DEFAULT 'mute'",
                "censor_punish_duration": "INTEGER DEFAULT 180",
                "lockdown_enabled": "INTEGER DEFAULT 0"
            }
            
            for col_name, col_def in new_cols.items():
                if col_name not in max_col_names:
                    print(f"Migrating database: Adding {col_name} to chats...")
                    await db.execute(f"ALTER TABLE chats ADD COLUMN {col_name} {col_def}")
                    
        await db.commit()

def get_db():
    return aiosqlite.connect(DB_PATH)
