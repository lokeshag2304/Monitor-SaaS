import sqlite3
db_path = "data/monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='check_results';")
if cursor.fetchone():
    print("Table 'check_results' exists")
    cursor.execute("PRAGMA table_info(check_results);")
    for col in cursor.fetchall(): print(f"  Col: {col[1]}")
else:
    print("Table 'check_results' does not exist")
conn.close()
