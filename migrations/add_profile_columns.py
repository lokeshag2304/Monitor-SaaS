import sqlite3

def upgrade_db():
    conn = sqlite3.connect("data/monitoring.db")
    cursor = conn.cursor()
    
    # Try adding new columns
    columns = [
        ("phone", "VARCHAR(20)"),
        ("company", "VARCHAR(100)"),
        ("timezone", "VARCHAR(50) DEFAULT 'UTC'"),
        ("notification_preferences", "VARCHAR(255) DEFAULT 'email'"),
        ("default_check_interval", "INTEGER DEFAULT 5")
    ]
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name} successfully.")
        except sqlite3.OperationalError as e:
            print(f"Column {col_name} might already exist or error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_db()
