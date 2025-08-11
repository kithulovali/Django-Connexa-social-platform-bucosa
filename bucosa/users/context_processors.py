from users.models_private_message import PrivateMessage

def unread_messages_count(request):
    if request.user.is_authenticated:
        return {'unread_messages_count': PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()}
    return {'unread_messages_count': 0}
