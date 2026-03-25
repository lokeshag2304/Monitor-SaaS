import sqlite3
import os
from backend.database import init_db

db_path = os.path.join(os.path.dirname(__file__), "data", "monitoring.db")

# First, run init_db to create the new tables (StatusPage, MonitorStatusHistory)
init_db()

# Second, manually alter incidents table because init_db won't do it for existing tables
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    columns_to_add = [
        ("user_id", "INTEGER"),
        ("monitor_name", "VARCHAR(255)"),
        ("previous_status", "VARCHAR(50)"),
        ("new_status", "VARCHAR(50)"),
        ("duration_seconds", "FLOAT"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ]
    for col_name, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE incidents ADD COLUMN {col_name} {col_def}")
            print(f"Added column {col_name} to incidents")
        except sqlite3.OperationalError as e:
            print(f"Column {col_name} might already exist: {e}")
            
    conn.commit()
    conn.close()
    print("Database models successfully migrated.")
except Exception as e:
    print(f"Failed to patch DB: {e}")
