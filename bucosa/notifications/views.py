from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Notification
from .tasks import send_notification_task

def send_notification_view(request):
    if request.method == 'POST':
        sender = request.user
        recipient_id = request.POST.get('recipient_id')
        notification_type = request.POST.get('notification_type', 'other')
        message = request.POST.get('message', '')
        User = get_user_model()
        try:
            recipient = User.objects.get(id=recipient_id)
            notification = Notification.objects.create(
                sender=sender,
                recipient=recipient,
                notification_type=notification_type,
                message=message
            )
            return JsonResponse({'status': 'success'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Recipient not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
