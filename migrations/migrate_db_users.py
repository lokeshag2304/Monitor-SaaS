import sqlite3
conn = sqlite3.connect('data/monitoring.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
    conn.commit()
    print("Column added")
except Exception as e:
    print(e)
conn.close()
