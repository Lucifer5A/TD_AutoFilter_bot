# Don't Remove Credit Tg - @TDBotDev
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@TDBotDev
# Ask Doubt on telegram https://t.me/TDBotDev
# =================================================================
import os
import random
from dotenv import load_dotenv

# config.py
load_dotenv()

def get_int(key, default):
    val = os.environ.get(key)
    if val:
        try:
            return int(val.strip())
        except ValueError:
            pass
    return default

API_ID = get_int("API_ID", 28961091)
API_HASH = os.environ.get("API_HASH", "fa3796dbdec1efdf151aca5f14815d06")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8439412197:AAHrIW_hH48tkimWzEZHivEOYOdQTcmmilM")

# =================================================================
# Search Settings
db_CHANNEL_ID = get_int("db_CHANNEL_ID", -1003823067419)

# =================================================================
START_TEXT = """
**🎬 Welcome to Movie & Anime Search Bot!**

**Find movies, series, and files instantly — fast, simple, and reliable.**

✨ **What you get:**
• ⚡ Fast and accurate results 
• 📜 movie, Animes & Cartoon 
• 🔥 Premium quality content  
• 📱 Seamless user experience  
• 🔒 Secure and private usage  

**Ready? Send a movie name to begin 👇**

*Example: Avengers Endgame*
"""
# =================================================================

MAX_RESULTS = int(os.environ.get("MAX_RESULTS", 10))

# Database Settings
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://tdanimehub_db_user:cPdMT253KSZpE11Z@helper.wallqjf.mongodb.net/?retryWrites=true&w=majority&appName=Helper")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "autofilebot")
COLLECTION_NAME = "files"

# =================================================================
# Optional settings
OWNER_ID = get_int("OWNER_ID", 1573111356)
ADMINS = [int(x.strip()) for x in os.environ.get("ADMINS", "1573111356").split(",") if x.strip()]

# =================================================================
# Force Subscribe Settings
# Updated to -1002497059972 as per user request
FORCE_SUB_CHANNELS = [int(x.strip()) for x in os.environ.get("FORCE_SUB_CHANNELS", "-1002497059972").split(",") if x.strip()]
ADMIN_IDS = ADMINS + [OWNER_ID]
FORCE_SUB_TEXT = os.environ.get("FORCE_SUB_TEXT", "📥 **Please join our channels to use this bot!**\n\nDue to high server load, only subscribers can search files.")

# =================================================================
# UI Images
PICS = [
    "https://ibb.co/39zW3dNh",
    "https://ibb.co/v4FX9rMN",
    "https://ibb.co/8L9rDmB4",
    "https://ibb.co/kVTGm4Rn",
    "https://ibb.co/Hff6FyNH",
    "https://ibb.co/DDRzKfv5",
    "https://ibb.co/Y7ds8xGg",
    "https://ibb.co/0jY0HHND",
    "https://ibb.co/Z1kCz73X"
]

def get_random_pic():
    return random.choice(PICS)

# Initial images
START_PIC = PICS[0]
FORCE_PIC = PICS[1]

# =================================================================
# Don't Remove Credit Tg - @TDBotDev
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@TDBotDev
# Ask Doubt on telegram https://t.me/TDBotDev
