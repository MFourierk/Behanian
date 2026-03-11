from .models import Configuration

def complexe_details(request):
    """Rend les détails de la configuration du complexe disponibles dans tous les templates."""
    if request.path.startswith('/admin/'):
        return {}
    return {'complexe': Configuration.load()}
