import asyncio
import mongomock
from database import add_file, get_unique_series, get_series_files, clean_series_name
import database
from unittest.mock import MagicMock

class MockMotorCollection:
    def __init__(self, collection):
        self.collection = collection
    async def update_one(self, filter, update, upsert=False):
        self.collection.update_one(filter, update, upsert=upsert)
    def find(self, filter, projection=None):
        cursor = self.collection.find(filter, projection)
        return MockMotorCursor(cursor)
    async def find_one(self, filter):
        return self.collection.find_one(filter)
    async def count_documents(self, filter):
        return self.collection.count_documents(filter)
    async def distinct(self, key):
        return self.collection.distinct(key)

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
        if length is None: return list(self.cursor)
        return list(self.cursor[:length])
    def __aiter__(self):
        self.iter_cursor = iter(self.cursor)
        return self
    async def __anext__(self):
        try: return next(self.iter_cursor)
        except StopIteration: raise StopAsyncIteration

async def test_normalization():
    # Test normalization rules
    assert clean_series_name("Naruto S01E01 Telugu.mkv") == "naruto"
    assert clean_series_name("One Piece Season 2 Episode 5 [1080p].mp4") == "one piece"
    assert clean_series_name("Session 01 Movie.mkv") == "movie"

async def test_grouping():
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['test_db']
    mock_collection = mock_db['files']
    database.collection = MockMotorCollection(mock_collection)

    await add_file("f1", "Naruto S01E01.mkv", None)
    await add_file("f2", "Naruto S02E01.mkv", None)
    await add_file("f3", "One Piece S01E01.mkv", None)

    # Unique series
    series = await get_unique_series()
    assert series == ["Naruto", "One Piece"]

    # Files for series
    naruto_files = await get_series_files("Naruto")
    assert len(naruto_files) == 2

    print("Grouping and Normalization tests passed!")

if __name__ == "__main__":
    asyncio.run(test_normalization())
    asyncio.run(test_grouping())
