"""
Behanian — Backup local vers D:\\.behanian\\backups
=================================================
Télécharge les backups du VPS vers le disque D: local (dossier caché).
Rétention : 90 jours de backups quotidiens + backups mensuels permanents.

Lancement automatique via Planificateur de tâches Windows.
Usage manuel : python backup_local.py [--verbose]
"""

import sys, os, re
from pathlib import Path
from datetime import date, timedelta, datetime

# Credentials lus depuis sync_laptop.py (évite la duplication)
import importlib.util as _ilu, pathlib as _pl
_spec = _ilu.spec_from_file_location("sync_laptop", _pl.Path(__file__).parent / "sync_laptop.py")
_sl   = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_sl)
VPS_HOST       = _sl.VPS_HOST
VPS_USER       = _sl.VPS_USER
VPS_PASSWORD   = _sl.VPS_PASSWORD
VPS_BACKUP_DIR = "/opt/behanian/backups"

LOCAL_BASE    = Path(r"D:\.behanian")
LOCAL_DAILY   = LOCAL_BASE / "backups" / "daily"
LOCAL_MONTHLY = LOCAL_BASE / "backups" / "monthly"
LOG_FILE      = LOCAL_BASE / "backup.log"

KEEP_DAILY_DAYS    = 90
KEEP_MONTHLY_YEARS = 5

VERBOSE = "--verbose" in sys.argv


def log(msg):
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def setup_dirs():
    for d in [LOCAL_DAILY, LOCAL_MONTHLY]:
        d.mkdir(parents=True, exist_ok=True)
    try:
        import subprocess
        subprocess.run(["attrib", "+H", str(LOCAL_BASE)], check=False, capture_output=True)
    except Exception:
        pass


def connect_vps():
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASSWORD, timeout=20)
    return ssh


def list_vps_backups(ssh):
    _, out, _ = ssh.exec_command(f"ls -1t {VPS_BACKUP_DIR}/backup_*.sql 2>/dev/null")
    return [f.strip() for f in out.read().decode().splitlines() if f.strip()]


def download_if_needed(sftp, remote_path, local_path):
    local_path = Path(local_path)
    try:
        remote_size = sftp.stat(remote_path).st_size
    except Exception:
        return False
    if local_path.exists() and local_path.stat().st_size == remote_size:
        if VERBOSE:
            log(f"  Déjà à jour : {local_path.name}")
        return False
    log(f"  Téléchargement : {Path(remote_path).name} ...")
    sftp.get(remote_path, str(local_path))
    size_kb = local_path.stat().st_size // 1024
    log(f"  OK — {local_path.name} ({size_kb} Ko)")
    return True


def purge_old(folder, keep_days):
    cutoff = date.today() - timedelta(days=keep_days)
    deleted = 0
    for f in Path(folder).glob("backup_*.sql"):
        m = re.search(r'backup_(\d{4})(\d{2})(\d{2})', f.name)
        if not m:
            continue
        file_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if file_date < cutoff:
            f.unlink()
            deleted += 1
            if VERBOSE:
                log(f"  Purgé : {f.name}")
    if deleted:
        log(f"  Purge {Path(folder).name}/ : {deleted} fichier(s) supprimé(s)")


def main():
    log("=" * 55)
    log("  Behanian Backup Local — Début")
    log("=" * 55)
    setup_dirs()

    try:
        import paramiko
    except ImportError:
        log("ERREUR : paramiko manquant. Lancez : pip install paramiko")
        sys.exit(1)

    log("Connexion VPS...")
    try:
        ssh = connect_vps()
    except Exception as e:
        log(f"ERREUR connexion VPS : {e}")
        sys.exit(1)
    log("Connexion OK")

    sftp = ssh.open_sftp()
    vps_files = list_vps_backups(ssh)

    if not vps_files:
        log("AVERTISSEMENT : aucun backup trouvé sur le VPS")
        sftp.close(); ssh.close(); return

    log(f"{len(vps_files)} backup(s) disponible(s) sur le VPS")

    # 1. Les 8 derniers fichiers VPS → daily (couvre environ 2 jours × 4/j)
    downloaded = 0
    for remote_path in vps_files[:8]:
        local_path = LOCAL_DAILY / Path(remote_path).name
        try:
            if download_if_needed(sftp, remote_path, local_path):
                downloaded += 1
        except Exception as e:
            log(f"  AVERTISSEMENT : {Path(remote_path).name} ignoré ({e})")

    # 2. Backup mensuel : un fichier par mois (si absent)
    today = date.today()
    monthly_name = f"backup_{today.strftime('%Y%m')}_mensuel.sql"
    monthly_path = LOCAL_MONTHLY / monthly_name
    if not monthly_path.exists():
        latest = vps_files[0]
        log(f"Backup mensuel {today.strftime('%Y-%m')} manquant — téléchargement...")
        try:
            sftp.get(latest, str(monthly_path))
            size_kb = monthly_path.stat().st_size // 1024
            log(f"  Mensuel OK — {monthly_name} ({size_kb} Ko)")
        except Exception as e:
            log(f"  ERREUR backup mensuel : {e}")

    sftp.close()
    ssh.close()

    # 3. Purge
    purge_old(LOCAL_DAILY, KEEP_DAILY_DAYS)
    purge_old(LOCAL_MONTHLY, KEEP_MONTHLY_YEARS * 365)

    # 4. Résumé
    nb_daily   = len(list(LOCAL_DAILY.glob("*.sql")))
    nb_monthly = len(list(LOCAL_MONTHLY.glob("*.sql")))
    total_mb   = sum(f.stat().st_size for f in LOCAL_BASE.rglob("*.sql")) / 1_048_576
    log(f"Résumé : {nb_daily} quotidien(s), {nb_monthly} mensuel(s) — {total_mb:.1f} Mo sur D:")
    log("Backup terminé avec succès")
    log("")


if __name__ == "__main__":
    main()
