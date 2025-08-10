from django.contrib.auth.decorators import login_required

# Notifications list page
@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'notifications/notifications_list.html', {'notifications': notifications})
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Notification
from .tasks import send_notification_task
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

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


# Mark all notifications as read (POST only)
@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)