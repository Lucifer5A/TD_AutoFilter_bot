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

async def add_file(file_id, file_name, caption):
    await collection.update_one(
        {"file_id": file_id},
        {"$set": {
            "file_name": file_name,
            "caption": caption or file_name
        }},
        upsert=True
    )

async def search_files_fuzzy(query, quality=None, language=None, skip=0, limit=10):
    # Construct an array of required patterns (Query AND (Lang OR Qual))
    # Requirement: "Build regex pattern from selected language + quality" and "Combine patterns using OR (|)"
    # Example: telugu + 720p -> "tel|telu|te|telugu|720|72|720p"
    # To satisfy both search accuracy and the prompt's OR logic:
    # We want results that contain the query AND match the fuzzy filter pattern.

    filter_patterns = []
    if quality and quality.lower() in QUAL_MAP:
        filter_patterns.extend(QUAL_MAP[quality.lower()])
    if language and language.lower() in LANG_MAP:
        filter_patterns.extend(LANG_MAP[language.lower()])

    # Base query filter
    mongo_filter = {"file_name": {"$regex": re.escape(query), "$options": "i"}}

    if filter_patterns:
        # Construct the OR part for quality/language
        # Order-independent: ensure the combined pattern exists
        combined_filters = "|".join([re.escape(x) for x in filter_patterns])
        mongo_filter["$and"] = [
            {"file_name": {"$regex": re.escape(query), "$options": "i"}},
            {"file_name": {"$regex": combined_filters, "$options": "i"}}
        ]

    total_count = await collection.count_documents(mongo_filter)
    cursor = collection.find(mongo_filter).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)

    return results, total_count

async def get_file_by_db_id(db_id):
    try:
        result = await collection.find_one({"_id": ObjectId(db_id)})
        return result
    except Exception:
        return None
