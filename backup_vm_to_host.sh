#!/bin/bash
# Behanian — Backup VM Ubuntu -> D:\.behanian\ du Windows host (VMware)
# ======================================================================
# Ce script tourne sur l'Ubuntu VM (complexe).
# Il fait un pg_dump local et copie vers le dossier partagé VMware
# monté sur le Windows host à D:\.behanian\
#
# Setup (une seule fois) :
#   1. VMware : VM Settings -> Options -> Shared Folders -> Add
#      Name  : Behanian_backup
#      Path  : D:\.behanian    (sur le Windows host)
#   2. Sur Ubuntu VM : sudo apt-get install -y open-vm-tools
#   3. Placer ce script sur la VM : /opt/behanian/backup_vm_to_host.sh
#   4. chmod +x /opt/behanian/backup_vm_to_host.sh
#   5. Ajouter au cron (sudo crontab -e) :
#      0 1,7,13,19 * * * /opt/behanian/backup_vm_to_host.sh
#      (4x par jour : 01h, 07h, 13h, 19h)
#
set -euo pipefail

# Configuration — credentials lus depuis Django settings (évite de les dupliquer)
DJANGO_DIR="/opt/behanian"
DB_USER=$(cd "$DJANGO_DIR" && source venv/bin/activate && \
    python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','behanian.settings'); \
    django.setup(); from django.conf import settings; \
    print(settings.DATABASES['default']['USER'])" 2>/dev/null || echo "behanian_user")
DB_PASS=$(cd "$DJANGO_DIR" && source venv/bin/activate && \
    python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','behanian.settings'); \
    django.setup(); from django.conf import settings; \
    print(settings.DATABASES['default']['PASSWORD'])" 2>/dev/null || echo "")
DB_NAME=$(cd "$DJANGO_DIR" && source venv/bin/activate && \
    python -c "import django,os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','behanian.settings'); \
    django.setup(); from django.conf import settings; \
    print(settings.DATABASES['default']['NAME'])" 2>/dev/null || echo "behanian_db")

HGFS_MOUNT="/mnt/hgfs/Behanian_backup"
DAILY_DIR="$HGFS_MOUNT/daily"
MONTHLY_DIR="$HGFS_MOUNT/monthly"
LOG_FILE="$HGFS_MOUNT/backup_vm.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TAILLE_MIN=150000
KEEP_DAILY_DAYS=90

log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOG_FILE" 2>/dev/null || echo "$(date '+%Y-%m-%d %H:%M:%S')  $*"; }

# 1. Vérifier que le dossier partagé VMware est monté
if [ ! -d "$HGFS_MOUNT" ]; then
    echo "ERREUR: $HGFS_MOUNT introuvable. VMware shared folder non monté." >&2
    # Tenter de remonter hgfs
    sudo vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other,uid=$(id -u),gid=$(id -g) 2>/dev/null || true
    sleep 2
    if [ ! -d "$HGFS_MOUNT" ]; then
        echo "ERREUR: Remontage échoué. Vérifiez VMware Shared Folders." >&2
        exit 1
    fi
fi

mkdir -p "$DAILY_DIR" "$MONTHLY_DIR"
log "=== Début backup VM -> Windows host ==="

# 2. pg_dump local
DUMP_FILE="/tmp/behanian_vm_${TIMESTAMP}.sql"
log "pg_dump..."
PGPASSWORD="$DB_PASS" pg_dump -U "$DB_USER" -h localhost "$DB_NAME" \
    --no-owner --no-acl > "$DUMP_FILE"

TAILLE=$(wc -c < "$DUMP_FILE")
if [ "$TAILLE" -lt "$TAILLE_MIN" ]; then
    log "ERREUR: Dump trop petit ($TAILLE octets). Backup annulé."
    rm -f "$DUMP_FILE"; exit 1
fi
log "Dump OK — $(du -sh "$DUMP_FILE" | cut -f1)"

# 3. Copie vers daily/
DEST="$DAILY_DIR/backup_${TIMESTAMP}.sql"
cp "$DUMP_FILE" "$DEST"
log "Copié -> $DEST"

# 4. Backup mensuel (un par mois)
MONTH_FILE="$MONTHLY_DIR/backup_$(date +%Y%m)_mensuel.sql"
if [ ! -f "$MONTH_FILE" ]; then
    cp "$DUMP_FILE" "$MONTH_FILE"
    log "Backup mensuel -> $MONTH_FILE"
fi

# 5. Nettoyage dump temporaire
rm -f "$DUMP_FILE"

# 6. Purge des backups quotidiens > 90 jours
find "$DAILY_DIR" -name "backup_*.sql" -mtime +${KEEP_DAILY_DAYS} -delete 2>/dev/null || true
# Purge des mensuels > 5 ans
find "$MONTHLY_DIR" -name "backup_*_mensuel.sql" -mtime +1825 -delete 2>/dev/null || true

# 7. Résumé
NB_D=$(ls "$DAILY_DIR"/*.sql 2>/dev/null | wc -l || echo 0)
NB_M=$(ls "$MONTHLY_DIR"/*.sql 2>/dev/null | wc -l || echo 0)
SIZE=$(du -sh "$HGFS_MOUNT" 2>/dev/null | cut -f1 || echo "?")
log "Résumé : $NB_D quotidien(s), $NB_M mensuel(s) — $SIZE sur D:"
log "=== Backup terminé ==="
log ""
