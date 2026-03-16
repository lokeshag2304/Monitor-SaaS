import sqlite3
db_path = "data/monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='status_pages';")
if cursor.fetchone():
    print("Table 'status_pages' exists")
    cursor.execute("PRAGMA table_info(status_pages);")
    for col in cursor.fetchall(): print(f"  Col: {col[1]}")
else:
    print("Table 'status_pages' does not exist")
conn.close()
