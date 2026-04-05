import mongomock
from database import add_file, search_files, get_file_by_db_id
import database

def test_mongodb_logic():
    # Use mongomock to simulate MongoDB
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['test_db']
    mock_collection = mock_db['files']

    # Overwrite database module collection for testing
    database.collection = mock_collection

    # Test adding files
    add_file("file_id_1", "The Dark Knight.mkv")
    add_file("file_id_2", "Interstellar.mp4")
    add_file("file_id_3", "Inception.mp4")

    # Test search (regex)
    results = search_files("Knight")
    assert len(results) == 1
    assert results[0]['file_name'] == "The Dark Knight.mkv"

    results = search_files("mp4")
    assert len(results) == 2

    # Test get by database _id
    db_id = str(results[0]['_id'])
    file_info = get_file_by_db_id(db_id)
    assert file_info['file_name'] == results[0]['file_name']

    # Test upsert
    add_file("file_id_1", "The Dark Knight Rises.mkv")
    # Search again
    results = search_files("Knight")
    assert results[0]['file_name'] == "The Dark Knight Rises.mkv"

    print("MongoDB logic tests with mongomock passed!")

if __name__ == "__main__":
    test_mongodb_logic()
