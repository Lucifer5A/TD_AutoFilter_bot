import os

# config.py

API_ID = int(os.environ.get("API_ID", 28961091))
API_HASH = os.environ.get("API_HASH", "fa3796dbdec1efdf151aca5f14815d06")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8579277980:AAHySce2PTH3JQM7stgcUlj59njtfueILx4")

# Search Settings
db_CHANNEL_ID = int(os.environ.get("db_CHANNEL_ID", -1002598623129))
START_TEXT = os.environ.get("START_TEXT", "🚀 Welcome to CineVerse Ultra\n\n🎬 Movies • Series • Anime • Episodes — All in One Place\n⚡ Lightning Fast Search with Smart Auto Filters\n🧠 Auto Detect Language • Quality • Seasons\n\n📂 Continue Watching • 🔥 Trending • ▶️ One Click Play\n\n🔍 Just send any name (movie / series / file) to start exploring")
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", 10))

# Database Settings
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://tdanimehub_db_user:cPdMT253KSZpE11Z@helper.wallqjf.mongodb.net/?retryWrites=true&w=majority&appName=Helper")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "autofilebot")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "files")

# Optional settings
OWNER_ID = int(os.environ.get("OWNER_ID", 1573111356))
ADMINS = [int(x) for x in os.environ.get("ADMINS", "1573111356").split(",") if x]
