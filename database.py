import re
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from bson.objectid import ObjectId

# Client and Collection initialization
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
nav_cache = db["nav_cache"]

# Allowed Mappings
LANG_MAP = {
    "Telugu": ["tel", "telu", "te", "telugu"],
    "Tamil": ["tam", "tami", "ta", "tamil"],
    "Hindi": ["hin", "hi", "hind", "hindi"],
    "English": ["eng", "en", "english"]
}

QUAL_MAP = {
    "480p": ["480", "48", "480p"],
    "720p": ["720", "72", "720p"],
    "1080p": ["1080", "108", "1080p"],
    "4K": ["4k", "2160p"]
}

# Regex patterns
PREFIX_PATTERN = re.compile(r"\[\s?@Team_TD_Links\s?\]", re.IGNORECASE)

def clean_ui_name(file_name):
    # Rule 4 & 5: NEVER show prefix in UI, show clean readable names
    name = PREFIX_PATTERN.sub("", file_name)
    return " ".join(name.split()).strip()

# Navigation Cache for Callback Data
async def save_nav_state(state_dict):
    key = hashlib.md5(str(state_dict).encode()).hexdigest()[:12]
    await nav_cache.update_one({"_id": key}, {"$set": state_dict}, upsert=True)
    return key

async def get_nav_state(key):
    return await nav_cache.find_one({"_id": key})

async def add_file(file_id, file_name, caption, message_id=None, channel_id=None, file_type=None):
    data = {
        "file_name": file_name,
        "caption": caption or file_name
    }
    if message_id: data["message_id"] = message_id
    if channel_id: data["channel_id"] = channel_id
    if file_type: data["file_type"] = file_type

    await collection.update_one(
        {"file_id": file_id},
        {"$set": data},
        upsert=True
    )

async def search_files_fuzzy(query, quality=None, language=None, skip=0, limit=10):
    mongo_filter = {"file_name": {"$regex": re.escape(query), "$options": "i"}}

    filter_patterns = []
    if quality and quality != "None":
        if quality in QUAL_MAP: filter_patterns.extend(QUAL_MAP[quality])

    if language and language != "None":
        if language in LANG_MAP:
            filter_patterns.extend(LANG_MAP[language])

    if filter_patterns:
        combined = "|".join([re.escape(x) for x in filter_patterns])
        mongo_filter["$and"] = [
            {"file_name": {"$regex": re.escape(query), "$options": "i"}},
            {"file_name": {"$regex": combined, "$options": "i"}}
        ]

    total_count = await collection.count_documents(mongo_filter)
    cursor = collection.find(mongo_filter).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    return results, total_count

async def get_file_by_db_id(db_id):
    try: return await collection.find_one({"_id": ObjectId(db_id)})
    except Exception: return None
