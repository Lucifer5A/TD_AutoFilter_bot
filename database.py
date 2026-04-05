import re
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from bson.objectid import ObjectId

# Client and Collection initialization
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Regex patterns for detection
SEASON_REGEX = re.compile(r"(S|Season|Session)\s?0?(\d{1,2})", re.IGNORECASE)
EPISODE_REGEX = re.compile(r"(E|Episode)\s?0?(\d{1,3})", re.IGNORECASE)

# Normalization cleaning patterns
CLEAN_PATTERNS = [
    SEASON_REGEX,
    EPISODE_REGEX,
    re.compile(r"\[.*?\]"),
    re.compile(r"\(.*?\)"),
    re.compile(r"\b(480p|720p|1080p|2160p|4k|hd|web\-dl|bluray|hdtv|x264|x265|hevc|mkv|mp4|avi)\b", re.IGNORECASE),
    re.compile(r"\b(telugu|tamil|hindi|english|malayalam|kannada|japanese|multi|dubbed|subbed|esub|dual|te|ta|hi|eng|kan|jap|mal)\b", re.IGNORECASE),
    re.compile(r"\b(19|20)\d{2}\b"),
]

def clean_series_name(file_name):
    # 1) SERIES NORMALIZATION (CRITICAL FIX)
    name = file_name.lower()
    for pattern in CLEAN_PATTERNS:
        name = pattern.sub("", name)
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    return " ".join(name.split()).strip()

async def add_file(file_id, file_name, caption, message_id=None, channel_id=None, file_type=None):
    cleaned_name = clean_series_name(file_name)
    data = {
        "file_name": file_name,
        "caption": caption or file_name,
        "cleaned_name": cleaned_name
    }
    if message_id: data["message_id"] = message_id
    if channel_id: data["channel_id"] = channel_id
    if file_type: data["file_type"] = file_type

    await collection.update_one(
        {"file_id": file_id},
        {"$set": data},
        upsert=True
    )

async def get_unique_series():
    # Use distinct on cleaned_name
    series = await collection.distinct("cleaned_name")
    return sorted([s.title() for s in series if s])

async def get_series_files(series_name):
    # Fetch all files matching the normalized name
    cursor = collection.find({"cleaned_name": series_name.lower()})
    return await cursor.to_list(length=None)

async def search_files_fuzzy(query, quality=None, language=None, skip=0, limit=10):
    # (Previously implemented fuzzy logic)
    from database import QUAL_MAP, LANG_MAP
    mongo_filter = {"file_name": {"$regex": re.escape(query), "$options": "i"}}

    filter_patterns = []
    if quality and quality.lower() in QUAL_MAP:
        filter_patterns.extend(QUAL_MAP[quality.lower()])
    if language and language.lower() in LANG_MAP:
        filter_patterns.extend(LANG_MAP[language.lower()])

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

# Helper Mappings for detection
LANG_MAP = {
    "telugu": ["tel", "telu", "te", "telugu"],
    "tamil": ["tam", "tami", "ta", "tamil"],
    "hindi": ["hin", "hi", "hind", "hindi"],
    "english": ["eng", "en", "english"],
    "malayalam": ["mal", "mala", "malayalam"],
    "kannada": ["kan", "kann", "kannada"],
    "japanese": ["jap", "japa", "japanese"]
}

QUAL_MAP = {
    "480p": ["480", "48", "480p"],
    "720p": ["720", "72", "720p"],
    "1080p": ["1080", "108", "1080p"],
    "4k": ["4k", "2160p"],
    "360p": ["360p", "360"]
}
