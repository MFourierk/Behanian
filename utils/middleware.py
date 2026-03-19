"""
Middleware de securite — neutralise is_staff, redirige vers home par groupe
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse, NoReverseMatch


HOME_BY_GROUP = {
    'Manager Général(e)':         'dashboard:index',
    'Manager General(e)':         'dashboard:index',
    'Manager Cuisine':            'cuisine:index',
    'Réceptionniste':             'hotel:index',
    'Receptionniste':             'hotel:index',
    'Caissière / Caissier':       'bar:tpe',
    'Caissiere / Caissier':       'bar:tpe',
    'Caissier(ère) Principal(e)': 'caisse:index',
    'Caissier(ere) Principal(e)': 'caisse:index',
    'Serveuse/Serveur':           'dashboard:index',
}

# Modules autorisés par groupe (pour vérification URL)
ALLOWED_PATHS = {
    'Manager Général(e)':         None,  # tout
    'Manager General(e)':         None,
    'Manager Cuisine':            ['/cuisine/'],
    'Réceptionniste':             ['/hotel/'],
    'Receptionniste':             ['/hotel/'],
    'Caissière / Caissier':       ['/bar/', '/restaurant/', '/piscine/', '/espaces-evenementiels/'],
    'Caissiere / Caissier':       ['/bar/', '/restaurant/', '/piscine/', '/espaces-evenementiels/'],
    'Caissier(ère) Principal(e)': ['/caisse/'],
    'Caissier(ere) Principal(e)': ['/caisse/'],
    'Serveuse/Serveur':           [],
}

ALWAYS_ALLOWED = ['/users/', '/static/', '/media/', '/dashboard/', '/admin/']


class StrictGroupAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated and not user.is_superuser:
            # Neutraliser is_staff
            if user.is_staff:
                user.is_staff = False

            # Bloquer /admin/
            if request.path.startswith('/admin/'):
                messages.error(request, "Accès administration refusé.")
                return redirect('dashboard:index')

            # Vérifier que le chemin est autorisé pour le groupe
            groups = list(user.groups.values_list('name', flat=True))
            if groups:
                for group in groups:
                    allowed = ALLOWED_PATHS.get(group)
                    if allowed is None:
                        break  # Manager Général — tout autorisé
                    # Toujours autoriser les chemins communs
                    path = request.path
                    if any(path.startswith(a) for a in ALWAYS_ALLOWED):
                        break
                    # Vérifier si le chemin est autorisé
                    if not any(path.startswith(a) for a in allowed):
                        home = HOME_BY_GROUP.get(group, 'dashboard:index')
                        try:
                            return redirect(home)
                        except NoReverseMatch:
                            return redirect('dashboard:index')

        return self.get_response(request)
