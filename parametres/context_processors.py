from .models import Coordonnees

def coordonnees_context(request):
    if request.path.startswith('/admin/'):
        return {}
    coordonnees = Coordonnees.objects.first()
    return {'coordonnees': coordonnees}
