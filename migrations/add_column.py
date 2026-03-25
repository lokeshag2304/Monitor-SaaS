import sqlite3
import os

db_path = r"c:\Users\Lokesh Agarwal\Desktop\Monitor-SaaS\data\monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE websites ADD COLUMN up_since DATETIME;")
    conn.commit()
    print("Column 'up_since' added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
finally:
    conn.close()
