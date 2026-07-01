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

# 0. Vérification préalable : complexe joignable via WireGuard
if ! ping -c 2 -W 5 10.8.0.2 > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: complexe (10.8.0.2) injoignable via WireGuard. Sync annulee." >> "$LOG"
    echo "---" >> "$LOG"
    exit 1
fi
if ! ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10 behanian@10.8.0.2 "echo ok" > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: SSH complexe echoue (WireGuard up mais SSH KO). Sync annulee." >> "$LOG"
    echo "---" >> "$LOG"
    exit 1
fi
echo "$(date '+%Y-%m-%d %H:%M:%S') --- Connexion complexe OK (ping + SSH)" >> "$LOG"

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

# SECURITE : verifier que auth_user est bien dans le dump ET contient des donnees
if ! grep -q "COPY public.auth_user" "$DUMP" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: Dump ne contient pas auth_user. Sync annulee." >> "$LOG"
    rm -f "$DUMP"
    exit 1
fi

# Compter les lignes de données dans auth_user (entre COPY ... FROM stdin; et \.)
NB_USERS_DUMP=$(awk '/^COPY public\.auth_user /,/^\\./{if(!/^COPY/ && !/^\\./)print}' "$DUMP" | wc -l | tr -d ' ')
if [ -z "$NB_USERS_DUMP" ] || [ "$NB_USERS_DUMP" -lt 3 ] 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: Dump auth_user ne contient que ${NB_USERS_DUMP:-0} utilisateur(s). Sync annulee." >> "$LOG"
    rm -f "$DUMP"
    exit 1
fi

SIZE=$(du -sh "$DUMP" | cut -f1)
echo "$(date '+%Y-%m-%d %H:%M:%S') --- Dump OK ($SIZE, ${TAILLE} octets, $NB_USERS_DUMP utilisateur(s) dans dump)" >> "$LOG"

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

# 8. Verification post-sync : base non vide
set +e
NB_USERS=$(PGPASSWORD='Beh@nian2026VPS' psql -U behanian_user -h localhost -d behanian_db -t -c "SELECT COUNT(*) FROM auth_user;" 2>/dev/null | tr -d ' \n')
set -e

if [ -z "$NB_USERS" ] || [ "$NB_USERS" -lt 1 ] 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ALERTE: ${NB_USERS:-0} utilisateur(s) apres sync. Restauration backup precedent..." >> "$LOG"

    # Chercher le backup precedent (exclu celui qu'on vient de creer)
    BACKUP_PRECEDENT=$(ls -t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | grep -v "^${BACKUP}$" | head -1 || true)

    if [ -n "${BACKUP_PRECEDENT:-}" ] && [ -f "$BACKUP_PRECEDENT" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') --- Restauration depuis : $(basename $BACKUP_PRECEDENT)" >> "$LOG"

        PGPASSWORD='Beh@nian2026VPS' psql -U behanian_user -h localhost -d behanian_db -c \
          "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO behanian_user; GRANT ALL ON SCHEMA public TO public;" >> "$LOG" 2>&1 || true

        PGPASSWORD='Beh@nian2026VPS' psql -U behanian_user -h localhost -d behanian_db \
          < "$BACKUP_PRECEDENT" >> "$LOG" 2>&1 || true

        python manage.py migrate --noinput >> "$LOG" 2>&1 || true

        set +e
        NB_FINAL=$(PGPASSWORD='Beh@nian2026VPS' psql -U behanian_user -h localhost -d behanian_db -t -c "SELECT COUNT(*) FROM auth_user;" 2>/dev/null | tr -d ' \n')
        set -e
        echo "$(date '+%Y-%m-%d %H:%M:%S') --- Restauration terminee : ${NB_FINAL:-0} utilisateur(s) restaure(s)" >> "$LOG"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') --- CRITIQUE: Aucun backup precedent disponible pour restauration!" >> "$LOG"
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- Verification OK : $NB_USERS utilisateur(s)" >> "$LOG"
fi

# 9. Redemarrer Gunicorn
sudo systemctl restart gunicorn

echo "$(date '+%Y-%m-%d %H:%M:%S') --- Sync + backup termines OK" >> "$LOG"
echo "---" >> "$LOG"
