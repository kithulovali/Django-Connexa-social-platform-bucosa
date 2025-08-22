from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Notification
from .tasks import send_notification_task
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
# Notifications list page
@login_required
def notifications_list(request):
    # Cache key generation
    cache_key = f'notifications_list_{request.user.id}'
    cached_response = cache.get(cache_key)
    
    if cached_response:
        return render(request, 'notifications/notifications_list.html', cached_response)
    
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    unread_notifications = notifications.filter(is_read=False)
    read_notifications = notifications.filter(is_read=True)
    unread_count = unread_notifications.count()
    # Get a set of user IDs that the current user is following
    followed_user_ids = set(request.user.following.values_list('following_user_id', flat=True))
    
    context = {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'unread_notification_count': unread_count,
        'followed_user_ids': followed_user_ids,
    }
    
    # Cache the response for 2 minutes
    cache.set(cache_key, context, 120)
    
    return render(request, 'notifications/notifications_list.html', context)


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

def api_unread_notifications_count(request):
    """API endpoint to get unread notification count for the logged-in user."""
    if not request.user.is_authenticated:
        return JsonResponse({'unread_notifications_count': 0})
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_notifications_count': count})

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)