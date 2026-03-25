import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "monitoring.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    columns_to_add = [
        ("region", "VARCHAR(50) DEFAULT 'Default'"),
        ("notifications", "VARCHAR(255) DEFAULT '[\"email\"]'"),
        ("timeout", "INTEGER DEFAULT 30"),
        ("keyword", "VARCHAR(255)"),
        ("ssl_check", "INTEGER DEFAULT 1"),
        ("redirect_follow", "INTEGER DEFAULT 1")
    ]
    for col_name, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE websites ADD COLUMN {col_name} {col_def}")
            print(f"Added column {col_name} successfully")
        except sqlite3.OperationalError as e:
            print(f"Column {col_name} might already exist: {e}")
    conn.commit()
    conn.close()
    print("DB migration applied successfully.")
except Exception as e:
    print(f"Failed to migrate DB: {e}")
