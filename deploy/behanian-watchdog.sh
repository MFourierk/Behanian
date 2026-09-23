#!/bin/bash
# Watchdog Behanian — vérifie gunicorn et la santé système
LOG=/var/log/behanian-watchdog.log

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# 1. Gunicorn actif selon systemd ?
if ! systemctl is-active --quiet gunicorn; then
    echo "$(ts) [WATCHDOG] gunicorn DOWN (systemd) — restart" >> "$LOG"
    systemctl restart gunicorn
    sleep 5
fi

# 2. Gunicorn répond-il vraiment aux requêtes HTTP ?
#    systemd peut dire "active" alors que les workers sont bloqués.
if ! curl -sf --max-time 8 http://127.0.0.1:8000/ -o /dev/null 2>/dev/null; then
    echo "$(ts) [WATCHDOG] gunicorn ne répond pas HTTP — restart" >> "$LOG"
    systemctl restart gunicorn
    sleep 5
fi

# 3. Mémoire disponible < 200 MiB → restart gunicorn
avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
if [ "$avail" -lt 204800 ]; then
    echo "$(ts) [WATCHDOG] RAM faible (${avail} kB dispo) — restart gunicorn" >> "$LOG"
    systemctl restart gunicorn
fi

# 4. Disque > 85% → alerte
used_pct=$(df /opt/behanian --output=pcent | tail -1 | tr -d ' %')
if [ "$used_pct" -gt 85 ]; then
    echo "$(ts) [WATCHDOG] DISQUE ALERTE ${used_pct}% sur /opt/behanian" >> "$LOG"
fi

# 5. Rotation log watchdog : garder les 500 dernières lignes
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 600 ]; then
    tail -500 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
fi
