import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
_owner_id = os.getenv("OWNER_ID", "0")
OWNER_ID = int(_owner_id) if _owner_id.isdigit() else 0

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN is not set in .env file!")
