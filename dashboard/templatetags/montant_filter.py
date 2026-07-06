from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter(name='qty')
def qty(value):
    """Affiche une quantité sans zéros inutiles : 1.000→1, 0.500→0.5, 1.250→1.25"""
    try:
        v = float(str(value).replace(',', '.').replace('\xa0', '').replace(' ', ''))
        if v == int(v):
            return str(int(v))
        s = f'{v:.10g}'
        return s
    except (ValueError, TypeError):
        return value


@register.filter(name='montant')
def montant(value, arg=0):
    """
    Formate un nombre avec une espace fine insécable comme séparateur de milliers.
    Usage : {{ valeur|montant }} ou {{ valeur|montant:2 }} pour 2 décimales.
    """
    try:
        decimals = int(arg)
        n = float(str(value).replace(' ', '').replace(' ', '').replace(' ', '').replace(',', '.'))
        # Formater avec virgule comme séparateur de groupe (Python), puis remplacer par espace fine
        if decimals == 0:
            formatted = f"{n:,.0f}".replace(',', ' ')
        else:
            formatted = f"{n:,.{decimals}f}".replace(',', ' ')
        return formatted
    except (ValueError, TypeError, InvalidOperation):
        return value
