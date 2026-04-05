import os
from database import init_db, add_file, search_files, get_file_by_id
from config import DATABASE_NAME

def test_database():
    # Remove existing db if any
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)

    init_db()

    # Test adding files
    add_file("file_id_1", "Avengers.mkv")
    add_file("file_id_2", "Batman.mp4")
    add_file("file_id_3", "Inception.mp4")

    # Test search
    results = search_files("Avenger")
    assert len(results) == 1
    assert results[0][1] == "Avengers.mkv"

    results = search_files("mp4")
    assert len(results) == 2

    results = search_files("None")
    assert len(results) == 0

    # Test get by ID
    db_id = search_files("Batman")[0][0]
    file_info = get_file_by_id(db_id)
    assert file_info[0] == "file_id_2"
    assert file_info[1] == "Batman.mp4"

    print("Database logic tests passed!")

if __name__ == "__main__":
    test_database()
