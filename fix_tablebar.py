import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS bar_tablebar;")
print("✅ Table bar_tablebar supprimée")

cursor.execute("PRAGMA table_info(bar_boncommandebar);")
columns = [row[1] for row in cursor.fetchall()]
print(f"Colonnes bar_boncommandebar: {columns}")

if 'capacite' in columns or 'zone' in columns:
    print("⚠️ Colonnes parasites détectées, correction...")
    cursor.execute("""
        CREATE TABLE bar_boncommandebar_new AS 
        SELECT id, fournisseur_id, numero, statut, date_commande, 
               date_reception_prevue, cree_par_id, date_creation
        FROM bar_boncommandebar;
    """)
    cursor.execute("DROP TABLE bar_boncommandebar;")
    cursor.execute("ALTER TABLE bar_boncommandebar_new RENAME TO bar_boncommandebar;")
    print("✅ Table bar_boncommandebar corrigée")
else:
    print("✅ Table bar_boncommandebar est propre")

cursor.execute("DELETE FROM django_migrations WHERE app='bar' AND name IN ('0003_tablebar_alter_boncommandebar_options_and_more', '0004_auto_20260311_1809');")
print("✅ Migrations corrompues supprimées")

conn.commit()
conn.close()
print("\n✅ Correction terminée !")