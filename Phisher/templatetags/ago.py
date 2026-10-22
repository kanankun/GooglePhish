"""Short relative time, for a table column.

Django's timesince gives "1 hour, 5 minutes", which is too wide next to a
clock time. This keeps the first unit only: "1h", "5m", "just now".
"""
from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def shortago(value):
    if not value:
        return ''
    seconds = int((timezone.now() - value).total_seconds())
    if seconds < 10:
        return 'just now'
    if seconds < 60:
        return f'{seconds}s ago'
    if seconds < 3600:
        return f'{seconds // 60}m ago'
    if seconds < 86400:
        return f'{seconds // 3600}h ago'
    return f'{seconds // 86400}d ago'
