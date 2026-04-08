import re
import hashlib
import asyncio
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

def clean_ui_name(file_name):
    """
    Cleans filename for UI display. Removes common tags and replaces separators with spaces.
    """
    # 1. Remove extension
    name = re.sub(r"\.(mkv|mp4|avi|webm|ts|m4v)$", "", file_name, flags=re.IGNORECASE)

    # 2. Remove specific known tags (Case Insensitive)
    tags_to_remove = [
        r"\[\s?@Team_TD_Links\s?\]",
        r"\[\s?Team\s?TD\s?Links\s?\]",
        r"\[\s?Team\s?\]",
        r"@Team_TD_Links",
        r"\[\s?HDRip\s?\]",
        r"\[\s?x264\s?\]",
        r"\[\s?720p\s?\]",
        r"\[\s?1080p\s?\]",
        r"\[\s?480p\s?\]"
    ]
    for tag in tags_to_remove:
        name = re.sub(tag, "", name, flags=re.IGNORECASE)

    # 3. Replace underscores and dots with spaces
    name = name.replace("_", " ").replace(".", " ")

    # 4. Clean up any remaining telegram handles (that didn't match specific tags)
    # But only if they are at the start or end to avoid eating movie names
    name = re.sub(r"^@\w+\s+", "", name)
    name = re.sub(r"\s+@\w+$", "", name)

    # 5. Final cleanup of double spaces and brackets
    name = name.replace("[ ]", "").replace("[]", "")
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
    # Fuzzy Search: "RRR movie" should match "RRR.2022.1080p"
    # Logic: ".*".join(query.split())
    fuzzy_query = ".*".join([re.escape(x) for x in query.split()])
    mongo_filter = {"file_name": {"$regex": fuzzy_query, "$options": "i"}}

    filter_patterns = []
    if quality and quality != "None":
        if quality in QUAL_MAP: filter_patterns.extend(QUAL_MAP[quality])

    if language and language != "None":
        if language in LANG_MAP:
            filter_patterns.extend(LANG_MAP[language])

    if filter_patterns:
        combined = "|".join([re.escape(x) for x in filter_patterns])
        mongo_filter["$and"] = [
            {"file_name": {"$regex": fuzzy_query, "$options": "i"}},
            {"file_name": {"$regex": combined, "$options": "i"}}
        ]

    # Use projection to fetch only required fields
    projection = {"file_name": 1, "file_id": 1, "_id": 1}

    # Run count and fetch in parallel for speed
    total_task = collection.count_documents(mongo_filter)
    results_task = collection.find(mongo_filter, projection).skip(skip).limit(limit).to_list(length=limit)

    total_count, results = await asyncio.gather(total_task, results_task)
    return results, total_count

async def get_file_by_db_id(db_id):
    try: return await collection.find_one({"_id": ObjectId(db_id)})
    except Exception: return None

async def delete_files_by_ids(file_ids):
    """Deletes documents matching provided file_ids."""
    try:
        res = await collection.delete_many({"file_id": {"$in": file_ids}})
        return res.deleted_count
    except Exception as e:
        print(f"DB Delete Error: {e}")
        return 0

async def delete_files_by_regex(query):
    """Deletes documents matching filename using fuzzy regex (consistent with search)."""
    try:
        fuzzy_query = ".*".join([re.escape(x) for x in query.split()])
        res = await collection.delete_many({"file_name": {"$regex": fuzzy_query, "$options": "i"}})
        return res.deleted_count
    except Exception as e:
        print(f"DB Delete Error: {e}")
        return 0
