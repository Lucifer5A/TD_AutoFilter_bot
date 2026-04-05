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

async def search_files(query, limit=10):
    # Escape query for regex to prevent injection/crashes
    escaped_query = re.escape(query)
    # Case-insensitive regex search
    cursor = collection.find(
        {"file_name": {"$regex": escaped_query, "$options": "i"}}
    )
    return await cursor.to_list(length=limit)

async def get_file_by_db_id(db_id):
    try:
        result = await collection.find_one({"_id": ObjectId(db_id)})
        return result
    except Exception:
        return None
