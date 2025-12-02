from django import template

register = template.Library()

@register.filter
def mul(a, b):
    try:
        return int(a) * int(b)
    except:
        return 0

@register.filter
def get_item(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return ""

@register.filter
def sum_values(d, key):
    if isinstance(d, dict):
        return sum(float(v.get(key, 0)) for v in d.values())
    return 0

@register.filter
def plus(a, b):
    try:
        return int(a) + int(b)
    except:
        return 0

@register.filter
def default_dash(value):
    return '-' if value in [None, ''] else value
