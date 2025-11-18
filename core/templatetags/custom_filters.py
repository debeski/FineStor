from django import template
from urllib.parse import urlencode



register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Safely get an item from a dictionary."""
    return dictionary.get(key)


@register.filter
def get_order(sort_option, order):
    return 'asc' if sort_option != 'number' or order == 'desc' else 'desc'


@register.filter
def set_value(value, new_value):
    return new_value


@register.filter
def is_in_group(user, group_name):
    """Check if a user is a member of a given group."""
    return user.groups.filter(name=group_name).exists()


@register.filter
def sum_total(assets):
    return sum(asset['total'] for asset in assets)


@register.filter
def has_non_sort_params(querydict, exclude_params=None):
    """
    Checks if the querydict contains keys other than those in exclude_params.
    """
    exclude_params = exclude_params or []
    for key in querydict.keys():
        if key not in exclude_params:
            return True
    return False


@register.filter
def build_query(params, exclude_keys=None):
    """
    Constructs a query string with only non-empty parameters.
    Optionally exclude specific keys.
    """
    exclude_keys = exclude_keys or []
    filtered_params = {key: value for key, value in params.items() if value and key not in exclude_keys}
    return urlencode(filtered_params)

