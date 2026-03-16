from django import template
from django.contrib.auth.models import User, Group

register = template.Library()

@register.filter
def get_serveurs(user):
    try:
        groupe = Group.objects.get(id=5)
        return groupe.user_set.all().order_by('first_name', 'username')
    except Group.DoesNotExist:
        return User.objects.none()
