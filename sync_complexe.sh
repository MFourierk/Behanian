#!/bin/bash
# Synchronisation Complexe (10.8.0.2) -> VPS + Sauvegarde SQL horodatee
# Cron : 0 */6 * * * et 30 22 * * *
set -euo pipefail

LOG="/opt/behanian/logs/sync.log"
BACKUP_DIR="/opt/behanian/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP="/tmp/behanian_sync_${TIMESTAMP}.sql"
BACKUP="$BACKUP_DIR/backup_${TIMESTAMP}.sql"
TAILLE_MIN=150000

echo "$(date '+%Y-%m-%d %H:%M:%S') --- Debut sync complexe->VPS" >> "$LOG"

# 1. Dump depuis le complexe via WireGuard
ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=30 behanian@10.8.0.2 \
  "PGPASSWORD='BehaNian2026Local' pg_dump -U behanian_user -h localhost behanian_db --no-owner --no-acl" \
  > "$DUMP"

# SECURITE : taille minimale du dump (150 Ko minimum)
TAILLE=$(wc -c < "$DUMP")
if [ "$TAILLE" -lt "$TAILLE_MIN" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: Dump trop petit ($TAILLE octets < $TAILLE_MIN). Sync annulee." >> "$LOG"
    rm -f "$DUMP"
    exit 1
fi

# SECURITE : verifier que auth_user est bien dans le dump
if ! grep -q "COPY public.auth_user" "$DUMP" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: Dump ne contient pas auth_user. Sync annulee." >> "$LOG"
    rm -f "$DUMP"
    exit 1
fi

SIZE=$(du -sh "$DUMP" | cut -f1)
echo "$(date '+%Y-%m-%d %H:%M:%S') --- Dump OK ($SIZE, ${TAILLE} octets)" >> "$LOG"

# 2. Copie de sauvegarde horodatee (conservee 7 jours)
cp "$DUMP" "$BACKUP"
echo "$(date '+%Y-%m-%d %H:%M:%S') --- Backup : $BACKUP" >> "$LOG"

# 3. Nettoyage des backups de plus de 7 jours
find "$BACKUP_DIR" -name "backup_*.sql"  -mtime +7 -delete
find "$BACKUP_DIR" -name "backup_*.json" -mtime +7 -delete
NB=$(ls "$BACKUP_DIR" | wc -l)
echo "$(date '+%Y-%m-%d %H:%M:%S') --- Backups conserves : $NB fichier(s)" >> "$LOG"

# 4. Reinitialiser le schema VPS
PGPASSWORD='Beh@nian2026VPS' psql -U behanian_user -h localhost -d behanian_db -c \
  "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO behanian_user; GRANT ALL ON SCHEMA public TO public;" >> "$LOG" 2>&1

# 5. Restaurer depuis le dump
PGPASSWORD='Beh@nian2026VPS' psql -U behanian_user -h localhost -d behanian_db < "$DUMP" >> "$LOG" 2>&1

# 6. Nettoyage dump temporaire
rm -f "$DUMP"

# 7. Migrations Django
cd /opt/behanian
source venv/bin/activate
python manage.py migrate --noinput >> "$LOG" 2>&1

# 8. Redemarrer Gunicorn
sudo systemctl restart gunicorn

echo "$(date '+%Y-%m-%d %H:%M:%S') --- Sync + backup termines OK" >> "$LOG"
echo "---" >> "$LOG"
