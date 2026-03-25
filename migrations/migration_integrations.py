import os
import sqlite3

def run():
    db_path = os.path.join("data", "monitoring.db")
    print(f"Applying integration migration to {db_path}...")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider VARCHAR(50) NOT NULL,
                config TEXT NOT NULL,
                is_enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS ix_integrations_user_id ON integrations (user_id)")
        
        conn.commit()
        print("Integration migration complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
