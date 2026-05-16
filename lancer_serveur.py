"""
Lancer le serveur Behanian avec Waitress (plus rapide que runserver)
Double-cliquez sur ce fichier ou lancez : python lancer_serveur.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

if __name__ == '__main__':
    import utils.py314_compat  # noqa: F401 — correction compatibilité Python 3.14
    from waitress import serve
    import django
    django.setup()
    from django.core.wsgi import get_wsgi_application

    app = get_wsgi_application()

    HOST = '127.0.0.1'
    PORT = 8000
    THREADS = 8  # 8 threads simultanés (vs 1 pour runserver)

    print(f"""
╔══════════════════════════════════════════╗
║   BEHANIAN - Complexe Hôtelier           ║
║   Serveur démarré sur http://{HOST}:{PORT} ║
║   Threads : {THREADS} (mode production)         ║
║   Ctrl+C pour arrêter                    ║
╚══════════════════════════════════════════╝
    """)

    serve(app, host=HOST, port=PORT, threads=THREADS)
