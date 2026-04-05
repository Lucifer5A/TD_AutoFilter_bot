import re
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from bson.objectid import ObjectId

# Client and Collection initialization
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

async def add_file(file_id, file_name, caption):
    # Ensure uniqueness using file_id
    await collection.update_one(
        {"file_id": file_id},
        {"$set": {
            "file_name": file_name,
            "caption": caption or file_name
        }},
        upsert=True
    )

async def search_files(query, filter_text=None, skip=0, limit=10):
    # Escape query and filter_text for regex
    escaped_query = re.escape(query)

    # Construct combined regex search if filter exists
    if filter_text:
        escaped_filter = re.escape(filter_text)
        # Search for query.*filter to find both in the file_name
        regex_pattern = f"{escaped_query}.*{escaped_filter}"
    else:
        regex_pattern = escaped_query

    # Case-insensitive regex search
    filter_obj = {"file_name": {"$regex": regex_pattern, "$options": "i"}}

    # Total count for pagination
    total_count = await collection.count_documents(filter_obj)

    # Fetch results with pagination
    cursor = collection.find(filter_obj).skip(skip).limit(limit)
    results = await cursor.to_list(length=limit)

    return results, total_count

async def get_file_by_db_id(db_id):
    try:
        result = await collection.find_one({"_id": ObjectId(db_id)})
        return result
    except Exception:
        return None
