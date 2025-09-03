# app/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get dictionary item safely"""
    return dictionary.get(key) if dictionary else None

@register.filter
def sum_actual(modes_dict):
    """Sum 'actual' marks in a modes dictionary"""
    if not modes_dict:
        return 0
    return sum(v.get('actual', 0) for v in modes_dict.values())


@register.filter
def sum_attr(dict_list, attr):
    """
    Sum a specific attribute from a list of dictionaries.
    Usage: {{ transaction.subjects|sum_attr:"full_marks" }}
    """
    if not dict_list:
        return 0
    return sum(d.get(attr, 0) for d in dict_list)