import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    cursor.execute("SELECT count(*) FROM facturation_article")
    count = cursor.fetchone()[0]
    print(f"Number of articles: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM facturation_article LIMIT 5")
        rows = cursor.fetchall()
        print("Sample data:")
        for row in rows:
            print(row)
except Exception as e:
    print(f"Error: {e}")

conn.close()
