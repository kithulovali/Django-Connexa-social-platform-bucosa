from django import template

def display_name(user):
    # If user has first and last name, use them
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}".strip()
    # If user has only first name
    if user.first_name:
        return user.first_name
    # If user has only last name
    if user.last_name:
        return user.last_name
    # Fallback to email if available
    if hasattr(user, 'email') and user.email:
        return user.email
    # Fallback to username
    return user.username

register = template.Library()
register.filter('display_name', display_name)
