"""
Middleware de sécurité — neutralise is_staff pour les non-superusers
Empêche l'accès à l'admin Django et aux vues protégées par is_staff
"""
from django.shortcuts import redirect
from django.contrib import messages


class StrictGroupAccessMiddleware:
    """
    Retire l'effet de is_staff pour les utilisateurs non-superuser.
    Seul le superuser a un accès étendu — tous les autres passent par les groupes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            # Neutraliser is_staff en session — ne pas modifier la DB
            if request.user.is_staff:
                # Masquer is_staff pour ce request uniquement
                request.user.is_staff = False

        # Bloquer l'accès à /admin/ pour les non-superusers
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            if not request.user.is_superuser:
                messages.error(request, "Accès à l'administration refusé.")
                return redirect('dashboard:index')

        return self.get_response(request)
