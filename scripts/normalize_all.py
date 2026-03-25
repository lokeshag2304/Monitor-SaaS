import sqlite3
import os

db_path = r"c:\Users\Lokesh Agarwal\Desktop\Monitor-SaaS\data\monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Normalizing websites.status...")
    cursor.execute("UPDATE websites SET status = UPPER(status)")
    print(f"Updated {cursor.rowcount} websites.")

    print("Normalizing users.role...")
    cursor.execute("UPDATE users SET role = UPPER(role)")
    print(f"Updated {cursor.rowcount} users.")

    print("Normalizing incidents previous_status/new_status...")
    cursor.execute("UPDATE incidents SET previous_status = UPPER(previous_status), new_status = UPPER(new_status)")
    print(f"Updated {cursor.rowcount} incidents.")

    print("Normalizing status_pages current_status...")
    cursor.execute("UPDATE status_pages SET current_status = UPPER(current_status)")
    print(f"Updated {cursor.rowcount} status pages.")

    print("Normalizing monitor_status_history status...")
    cursor.execute("UPDATE monitor_status_history SET status = UPPER(status)")
    print(f"Updated {cursor.rowcount} history records.")

    conn.commit()
    print("All normalization complete.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
