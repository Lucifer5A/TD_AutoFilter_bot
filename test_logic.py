import asyncio
import mongomock
from database import add_file, search_files, get_file_by_db_id
import database
from unittest.mock import MagicMock

# Mock Motor's AsyncIOMotorClient since mongomock is synchronous
class MockMotorCollection:
    def __init__(self, collection):
        self.collection = collection

    async def update_one(self, filter, update, upsert=False):
        self.collection.update_one(filter, update, upsert=upsert)

    def find(self, filter):
        cursor = self.collection.find(filter)
        return MockMotorCursor(cursor)

    async def find_one(self, filter):
        return self.collection.find_one(filter)

class MockMotorCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    async def to_list(self, length):
        return list(self.cursor[:length])

async def test_mongodb_logic():
    # Use mongomock to simulate MongoDB
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['test_db']
    mock_collection = mock_db['files']

    # Overwrite database module collection with our async mock wrapper
    database.collection = MockMotorCollection(mock_collection)

    # Test adding files with captions
    await add_file("file_id_1", "Movie.mkv", "This is a movie caption")
    await add_file("file_id_2", "Video.mp4", None) # Testing fallback

    # Test search
    results = await search_files("Movie")
    assert len(results) == 1
    assert results[0]['file_name'] == "Movie.mkv"
    assert results[0]['caption'] == "This is a movie caption"

    # Test get by database _id
    db_id = str(results[0]['_id'])
    file_info = await get_file_by_db_id(db_id)
    assert file_info['caption'] == "This is a movie caption"

    # Test fallback
    results = await search_files("Video")
    assert results[0]['caption'] == "Video.mp4"

    print("Async MongoDB logic tests with caption support passed!")

if __name__ == "__main__":
    asyncio.run(test_mongodb_logic())
