import sqlite3
db_path = "data/monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='incidents';")
result = cursor.fetchone()
if result:
    print(f"Table 'incidents' exists")
    cursor.execute("PRAGMA table_info(incidents);")
    cols = cursor.fetchall()
    for col in cols:
        print(f"  Col: {col[1]}")
else:
    print("Table 'incidents' does not exist")
conn.close()
