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

    async def count_documents(self, filter):
        return self.collection.count_documents(filter)

class MockMotorCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def skip(self, n):
        self.cursor = self.cursor[n:]
        return self

    def limit(self, n):
        self.cursor = self.cursor[:n]
        return self

    async def to_list(self, length):
        return list(self.cursor)

async def test_pagination_and_filters():
    # Use mongomock to simulate MongoDB
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['test_db']
    mock_collection = mock_db['files']

    # Overwrite database module collection with our async mock wrapper
    database.collection = MockMotorCollection(mock_collection)

    # Test adding files with various formats
    await add_file("f1", "Naruto S01 480p Telugu.mkv", None)
    await add_file("f2", "Naruto S01 720p Hindi.mkv", None)
    await add_file("f3", "Naruto S01 1080p English.mkv", None)
    await add_file("f4", "Naruto Movie 720p Telugu.mp4", None)
    await add_file("f5", "Naruto Movie 1080p Telugu.mp4", None)
    await add_file("f6", "Naruto Movie 480p English.mp4", None)

    # Test basic search and count
    results, total_results = await search_files("Naruto", limit=2)
    assert total_results == 6
    assert len(results) == 2

    # Test pagination (skip)
    results, total_results = await search_files("Naruto", skip=2, limit=2)
    assert total_results == 6
    assert len(results) == 2

    # Test filter (quality)
    results, total_results = await search_files("Naruto", filter_text="720p")
    assert total_results == 2
    assert "720p" in results[0]['file_name']

    # Test filter (language)
    results, total_results = await search_files("Naruto", filter_text="Telugu")
    assert total_results == 3
    for r in results:
        assert "Telugu" in r['file_name']

    # Test combined filter logic (query.*filter)
    # Search "Naruto Movie" with "Telugu"
    results, total_results = await search_files("Naruto Movie", filter_text="Telugu")
    assert total_results == 2

    print("Pagination and Filter database logic tests passed!")

if __name__ == "__main__":
    asyncio.run(test_pagination_and_filters())
