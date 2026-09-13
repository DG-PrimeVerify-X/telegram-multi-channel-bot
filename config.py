import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN=os.getenv("BOT_TOKEN","").strip()
OWNER_ID=int(os.getenv("OWNER_ID","0") or 0)
DB_PATH=os.getenv("DB_PATH","data/bot.db")
LOG_LEVEL=os.getenv("LOG_LEVEL","INFO")
