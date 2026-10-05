#!/bin/bash
# Déclencheur sync Complexe -> VPS
# Runs ON the complexe, SSHes TO the VPS and triggers sync_complexe.sh there.
# Cron : 0 2,12,18 * * *
set -euo pipefail

LOG="/opt/behanian/sync.log"
VPS_HOST="10.8.0.1"
VPS_USER="behanian"
VPS_KEY="$HOME/.ssh/vps_tunnel"
mkdir -p "$(dirname "$LOG")"

echo "$(date '+%Y-%m-%d %H:%M:%S') --- Debut sync_behanian -> VPS" >> "$LOG"

# 1. Test connectivité VPS
if ! ssh -i "$VPS_KEY" \
         -o StrictHostKeyChecking=no \
         -o BatchMode=yes \
         -o ConnectTimeout=15 \
         "$VPS_USER@$VPS_HOST" "echo ok" > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') --- ERREUR: VPS ($VPS_HOST) injoignable. Sync annulee." >> "$LOG"
    echo "---" >> "$LOG"
    exit 1
fi

# 2. Déclencher sync_complexe.sh sur le VPS
ssh -i "$VPS_KEY" \
    -o StrictHostKeyChecking=no \
    -o BatchMode=yes \
    -o ConnectTimeout=60 \
    "$VPS_USER@$VPS_HOST" \
    "/bin/bash /opt/behanian/sync_complexe.sh" >> "$LOG" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') --- sync_behanian OK" >> "$LOG"
echo "---" >> "$LOG"
