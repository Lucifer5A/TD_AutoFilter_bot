import sqlite3
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_file(file_id, file_name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO files (file_id, file_name) VALUES (?, ?)', (file_id, file_name))
    conn.commit()
    conn.close()

def search_files(query):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Using LIKE for case-insensitive search
    cursor.execute('SELECT id, file_name FROM files WHERE file_name LIKE ?', ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()
    return results

def get_file_by_id(db_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT file_id, file_name FROM files WHERE id = ?', (db_id,))
    result = cursor.fetchone()
    conn.close()
    return result

if __name__ == "__main__":
    init_db()
