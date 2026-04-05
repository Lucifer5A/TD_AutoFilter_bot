import asyncio
import mongomock
from database import add_file, search_files_fuzzy, get_file_by_db_id
import database
from unittest.mock import MagicMock

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

async def test_fuzzy_search():
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['test_db']
    mock_collection = mock_db['files']
    database.collection = MockMotorCollection(mock_collection)

    # Adding test data with various tags in different order
    await add_file("f1", "[720p] Naruto S01 Telugu.mkv", None)
    await add_file("f2", "Batman 480p Tamil.mp4", None)
    await add_file("f3", "Hindi Movie 1080p.mkv", None)

    # Test order independence: Naruto with Telugu (Telugu is in name)
    results, total = await search_files_fuzzy("Naruto", language="Telugu")
    assert total == 1

    # Test fuzzy matching: Tamil (ta, tam, tamil)
    results, total = await search_files_fuzzy("Batman", language="Tamil")
    assert total == 1

    # Test OR combined search: Search Batman with Tamil (should find 1)
    # Search Movie with 1080p (should find 1)
    results, total = await search_files_fuzzy("Movie", quality="1080p")
    assert total == 1

    print("Refined fuzzy search logic tests passed!")

if __name__ == "__main__":
    asyncio.run(test_fuzzy_search())
