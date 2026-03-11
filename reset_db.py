import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all facturation tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'facturation_%'")
tables = cursor.fetchall()

print("Tables to drop:")
for table in tables:
    print(f"- {table[0]}")

# Disable foreign key checks temporarily
cursor.execute("PRAGMA foreign_keys = OFF")

# Drop all facturation tables
for table in tables:
    try:
        cursor.execute(f"DROP TABLE {table[0]}")
        print(f"Dropped {table[0]}")
    except Exception as e:
        print(f"Error dropping {table[0]}: {e}")

# Remove migration history for facturation app
try:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'facturation'")
    print("Removed facturation migration history")
except Exception as e:
    print(f"Error removing migration history: {e}")

# Re-enable foreign key checks
cursor.execute("PRAGMA foreign_keys = ON")

conn.commit()
conn.close()

print("Database reset complete for facturation app")