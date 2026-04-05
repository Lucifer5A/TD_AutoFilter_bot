import asyncio
import mongomock
from database import add_file, get_unique_series, get_seasons, get_episodes, clean_series_name
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
        return list(self.cursor)
    def __aiter__(self):
        self.iter_cursor = iter(self.cursor)
        return self
    async def __anext__(self):
        try:
            return next(self.iter_cursor)
        except StopIteration:
            raise StopAsyncIteration

async def test_list_logic():
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['test_db']
    mock_collection = mock_db['files']
    database.collection = MockMotorCollection(mock_collection)

    # Test cleaning logic
    assert clean_series_name("Naruto S01E01 Telugu.mkv") == "Naruto"
    assert clean_series_name("One Piece [720p] [Multi] Season 1.mp4") == "One Piece"

    # Adding test data
    await add_file("f1", "Naruto S01E01.mkv", None)
    await add_file("f2", "Naruto Season 1 Episode 2.mp4", None)
    await add_file("f3", "Naruto S02E01.mkv", None)
    await add_file("f4", "One Piece [S01] [E01].mkv", None)

    # Test unique series extraction
    series = await get_unique_series()
    assert "Naruto" in series
    assert "One Piece" in series

    # Test season detection
    seasons = await get_seasons("Naruto")
    assert seasons == [1, 2]

    # Test episode detection and sorting
    episodes = await get_episodes("Naruto", 1)
    assert len(episodes) == 2
    assert episodes[0]['e_num'] == 1
    assert episodes[1]['e_num'] == 2

    print("List channel logic tests passed!")

if __name__ == "__main__":
    asyncio.run(test_list_logic())
