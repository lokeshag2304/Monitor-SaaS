import sqlite3
import os

def migrate():
    # Update for actually used DB path
    db_path = os.path.join(os.getcwd(), "data", "monitoring.db")
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating pagespeed_results table...")
    
    # Check current columns
    cursor.execute("PRAGMA table_info(pagespeed_results)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "status" not in columns:
        print("Adding 'status' column...")
        try:
            cursor.execute("ALTER TABLE pagespeed_results ADD COLUMN status VARCHAR DEFAULT 'UP'")
            print("Successfully added 'status' column.")
        except Exception as e:
            print(f"Error adding 'status' column: {e}")
    else:
        print("'status' column already exists.")

    if "fcp" not in columns:
        print("Adding 'fcp' column...")
        try:
            cursor.execute("ALTER TABLE pagespeed_results ADD COLUMN fcp FLOAT")
            print("Successfully added 'fcp' column.")
        except Exception as e:
            print(f"Error adding 'fcp' column: {e}")
    else:
        print("'fcp' column already exists.")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
