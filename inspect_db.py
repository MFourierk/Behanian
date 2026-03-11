import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("--- Schema of facturation_article ---")
try:
    cursor.execute("PRAGMA table_info(facturation_article)")
    columns = cursor.fetchall()
    if not columns:
        print("Table facturation_article does not exist.")
    else:
        for col in columns:
            print(col)
except Exception as e:
    print(f"Error: {e}")

conn.close()
