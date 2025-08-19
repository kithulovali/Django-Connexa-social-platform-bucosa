from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter
def user_by_id(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)
