import re
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from bson.objectid import ObjectId

# Client and Collection initialization
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Fuzzy Mappings
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
    "1080p": ["1080", "108", "1080p"]
}

# Regex patterns for cleaning and detection
SEASON_REGEX = re.compile(r"(S(\d{1,2})|Season\s?(\d+))", re.IGNORECASE)
EPISODE_REGEX = re.compile(r"(E(\d{1,3})|Episode\s?(\d+))", re.IGNORECASE)

# Patterns to remove for clean series name
CLEAN_PATTERNS = [
    re.compile(r"\[.*?\]"),
    re.compile(r"\(.*?\)"),
    re.compile(r"\b(480p|720p|1080p|2160p|4k|hd|web\-dl|bluray|hdtv|x264|x265|hevc|mkv|mp4|avi)\b", re.IGNORECASE),
    re.compile(r"\b(telugu|tamil|hindi|english|malayalam|kannada|japanese|multi|dubbed|subbed|esub|dual|te|ta|hi|eng|kan|jap|mal)\b", re.IGNORECASE),
    re.compile(r"\b(19|20)\d{2}\b"),
]

def clean_series_name(file_name):
    name = SEASON_REGEX.sub("", file_name)
    name = EPISODE_REGEX.sub("", name)
    for pattern in CLEAN_PATTERNS:
        name = pattern.sub("", name)
    name = re.sub(r"[^a-zA-Z0-9\s]", " ", name)
    return " ".join(name.split()).strip().title()

async def add_file(file_id, file_name, caption, message_id=None, channel_id=None, file_type=None):
    # Store cleaned_name to make /list_channel efficient
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

async def search_files_fuzzy(query, quality=None, language=None, skip=0, limit=10):
    filter_patterns = []
    if quality and quality.lower() in QUAL_MAP:
        filter_patterns.extend(QUAL_MAP[quality.lower()])
    if language and language.lower() in LANG_MAP:
        filter_patterns.extend(LANG_MAP[language.lower()])

    mongo_filter = {"file_name": {"$regex": re.escape(query), "$options": "i"}}
    if filter_patterns:
        combined_filters = "|".join([re.escape(x) for x in filter_patterns])
        mongo_filter["$and"] = [
            {"file_name": {"$regex": re.escape(query), "$options": "i"}},
            {"file_name": {"$regex": combined_filters, "$options": "i"}}
        ]

    total_count = await collection.count_documents(mongo_filter)
    cursor = collection.find(mongo_filter).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)
    return results, total_count

async def get_unique_series():
    # Efficient: use distinct on cleaned_name
    series = await collection.distinct("cleaned_name")
    return sorted([s for s in series if s])

async def get_seasons(series_name):
    # Efficient: search by cleaned_name
    cursor = collection.find({"cleaned_name": series_name}, {"file_name": 1})
    seasons = set()
    async for doc in cursor:
        match = SEASON_REGEX.search(doc["file_name"])
        if match:
            s_num = match.group(2) or match.group(3)
            if s_num: seasons.add(int(s_num))
    if not seasons: return [1]
    return sorted(list(seasons))

async def get_episodes(series_name, season_number):
    cursor = collection.find({"cleaned_name": series_name}, {"file_name": 1, "file_id": 1})
    episodes = []
    async for doc in cursor:
        s_match = SEASON_REGEX.search(doc["file_name"])
        current_s = int(s_match.group(2) or s_match.group(3)) if s_match else 1
        if current_s == season_number:
            e_match = EPISODE_REGEX.search(doc["file_name"])
            e_num = int(e_match.group(2) or e_match.group(3)) if e_match else 1
            episodes.append({
                "id": str(doc["_id"]),
                "file_id": doc["file_id"],
                "name": doc["file_name"],
                "e_num": e_num
            })
    return sorted(episodes, key=lambda x: x["e_num"])

async def get_file_by_db_id(db_id):
    try: return await collection.find_one({"_id": ObjectId(db_id)})
    except Exception: return None
