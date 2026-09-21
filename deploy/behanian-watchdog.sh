#!/bin/bash
# Watchdog Behanian — vérifie gunicorn et la santé système
LOG=/var/log/behanian-watchdog.log

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# Gunicorn
if ! systemctl is-active --quiet gunicorn; then
    echo "$(ts) [WATCHDOG] gunicorn DOWN — restart" >> "$LOG"
    systemctl restart gunicorn
fi

# Mémoire disponible (en kB) — redémarrer gunicorn si < 200 MiB disponibles
avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
if [ "$avail" -lt 204800 ]; then
    echo "$(ts) [WATCHDOG] RAM faible (${avail} kB dispo) — restart gunicorn" >> "$LOG"
    systemctl restart gunicorn
fi

# Disque — alerte si > 85 %
used_pct=$(df /opt/behanian --output=pcent | tail -1 | tr -d ' %')
if [ "$used_pct" -gt 85 ]; then
    echo "$(ts) [WATCHDOG] DISQUE ALERTE ${used_pct}% sur /opt/behanian" >> "$LOG"
fi

# Rotation simple du log watchdog : garder les 500 dernières lignes
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 600 ]; then
    tail -500 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
fi
