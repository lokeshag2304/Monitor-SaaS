import os
import sqlite3

def run():
    db_path = os.path.join("data", "monitoring.db")
    print(f"Applying migration to {db_path}...")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Drop existing old status_pages
        c.execute("DROP TABLE IF EXISTS status_pages")
        
        # New tables will be created cleanly by SQLAlchemy when the app boots or here
        c.execute("""
            CREATE TABLE status_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) NOT NULL UNIQUE,
                logo VARCHAR(1024),
                custom_message TEXT,
                created_by INTEGER NOT NULL,
                FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        c.execute("""
            CREATE TABLE status_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                status_page_id INTEGER NOT NULL,
                FOREIGN KEY(status_page_id) REFERENCES status_pages(id) ON DELETE CASCADE
            )
        """)
        
        c.execute("""
            CREATE TABLE status_group_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                monitor_id INTEGER NOT NULL,
                FOREIGN KEY(group_id) REFERENCES status_groups(id) ON DELETE CASCADE,
                FOREIGN KEY(monitor_id) REFERENCES websites(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Migration complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
