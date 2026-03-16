import sqlite3
db_path = "data/monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monitor_status_history';")
if cursor.fetchone():
    print("Table 'monitor_status_history' exists")
    cursor.execute("PRAGMA table_info(monitor_status_history);")
    for col in cursor.fetchall(): print(f"  Col: {col[1]}")
else:
    print("Table 'monitor_status_history' does not exist")
conn.close()
