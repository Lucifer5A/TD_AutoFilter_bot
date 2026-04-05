import re
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from bson.objectid import ObjectId

# Client and Collection initialization
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

async def add_file(file_id, file_name, caption):
    await collection.update_one(
        {"file_id": file_id},
        {"$set": {
            "file_name": file_name,
            "caption": caption or file_name
        }},
        upsert=True
    )

async def search_files_advanced(query, quality=None, language=None, skip=0, limit=10):
    # Escape parts
    q = re.escape(query)

    # Logic for combined filters
    if (quality and quality != "None") and (language and language != "None"):
        qual = re.escape(quality)
        lang = re.escape(language)
        # Requirement: query.*(telugu.*720p|720p.*telugu)
        regex_pattern = f"{q}.*({lang}.*{qual}|{qual}.*{lang})"
    elif quality and quality != "None":
        qual = re.escape(quality)
        regex_pattern = f"{q}.*{qual}"
    elif language and language != "None":
        lang = re.escape(language)
        regex_pattern = f"{q}.*{lang}"
    else:
        regex_pattern = q

    filter_obj = {"file_name": {"$regex": regex_pattern, "$options": "i"}}

    total_count = await collection.count_documents(filter_obj)
    cursor = collection.find(filter_obj).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)

    return results, total_count

async def get_file_by_db_id(db_id):
    try:
        result = await collection.find_one({"_id": ObjectId(db_id)})
        return result
    except Exception:
        return None
