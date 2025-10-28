from django import template

register = template.Library()

@register.filter
def get_total_notifications(dictionary, org_id_str):
    total = 0
    if not dictionary or not org_id_str:
        return 0

    for key, value in dictionary.items():
        if key.startswith(str(org_id_str)):
            if isinstance(value, dict):
                total += value.get('unapproved_count', 0)
            elif isinstance(value, int):
                total += value
    return total


@register.filter
def get_invoice_pending_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def get_nested(value, arg):
    """
    Handles both flat dotted keys and actual nested dict/objects.
    """
    try:
        # First try direct flat key (e.g., 'store_id.store_name')
        if isinstance(value, dict) and arg in value:
            return value[arg]

        # Then try nested access (e.g., item.store_id.store_name or nested dicts)
        for key in arg.split('.'):
            value = value.get(key) if isinstance(value, dict) else getattr(value, key, '')
        return value
    except Exception:
        return ''
    
@register.filter
def format_99plus_count(value):
    try:
        value = int(value)
        if value > 99:
            return "99+"
        return str(value)
    except (ValueError, TypeError):
        return "0"