from django import template

register = template.Library()

@register.filter
def display_name(user):
    if hasattr(user, 'get_full_name') and user.get_full_name():
        return user.get_full_name()
    return user.username
