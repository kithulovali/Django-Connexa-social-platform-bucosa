def get_display_name(user):
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}".strip()
    if user.first_name:
        return user.first_name
    if user.last_name:
        return user.last_name
    if hasattr(user, 'email') and user.email:
        return user.email
    return user.username
