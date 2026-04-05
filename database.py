import pymongo
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

# Client and Collection initialization
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def add_file(file_id, file_name):
    # Ensure uniqueness using file_id
    collection.update_one(
        {"file_id": file_id},
        {"$set": {"file_name": file_name}},
        upsert=True
    )

def search_files(query):
    # Case-insensitive regex search
    results = collection.find(
        {"file_name": {"$regex": query, "$options": "i"}}
    )
    return list(results)

def get_file_by_db_id(db_id):
    from bson.objectid import ObjectId
    try:
        result = collection.find_one({"_id": ObjectId(db_id)})
        return result
    except Exception:
        return None
