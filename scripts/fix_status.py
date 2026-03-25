import sqlite3
import os

db_path = r"c:\Users\Lokesh Agarwal\Desktop\Monitor-SaaS\data\monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("UPDATE websites SET status = UPPER(status)")
    conn.commit()
    print(f"Normalized {cursor.rowcount} statuses to UPPERCASE.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
