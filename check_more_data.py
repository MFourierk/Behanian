import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("--- LigneFacture ---")
try:
    cursor.execute("SELECT count(*) FROM facturation_lignefacture")
    print(f"Count: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error reading LigneFacture: {e}")

print("\n--- Client Schema ---")
try:
    cursor.execute("PRAGMA table_info(facturation_client)")
    for col in cursor.fetchall():
        print(col)
except Exception as e:
    print(f"Error reading Client schema: {e}")

conn.close()
