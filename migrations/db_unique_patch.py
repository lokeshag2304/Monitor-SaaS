import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "monitoring.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete duplicates keeping the newest one
    cursor.execute("""
        DELETE FROM websites 
        WHERE id NOT IN (
            SELECT MAX(id) 
            FROM websites 
            GROUP BY owner_id, url
        )
    """)
    
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_owner_url ON websites(owner_id, url)")
    conn.commit()
    conn.close()
    print("Database deduplicated and unique constraint applied successfully.")
except Exception as e:
    print(f"Error applying unique constraint: {e}")
