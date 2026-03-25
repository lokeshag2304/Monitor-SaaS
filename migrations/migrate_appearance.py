import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Correct path to the database
DATABASE_PATH = os.path.join(BASE_DIR, "data", "monitoring.db")

def migrate():
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    columns_to_add = [
        ("theme_mode", "TEXT DEFAULT 'dark'"),
        ("theme_color", "TEXT DEFAULT '#2563eb'"),
        ("glass_effect", "TEXT DEFAULT 'normal'"),
        ("background_alt", "TEXT DEFAULT '#020617'"),
        ("font_family", "TEXT DEFAULT 'Inter'")
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to users table.")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists.")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
