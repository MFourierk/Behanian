from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.inclusion_tag('components/breadcrumb.html', takes_context=True)
def breadcrumb(context, *args):
    items = []
    args = list(args)
    while len(args) >= 2:
        label    = args.pop(0)
        url_name = args.pop(0)
        if url_name:
            try:
                url = reverse(url_name)
                items.append({'label': label, 'url': url, 'active': False})
            except NoReverseMatch:
                items.append({'label': label, 'url': url_name, 'active': False})
        else:
            items.append({'label': label, 'url': None, 'active': True})
    return {'items': items}


@register.inclusion_tag('components/breadcrumb.html')
def breadcrumb_items(items):
    return {'items': items}
