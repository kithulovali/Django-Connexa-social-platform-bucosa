from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from users.models import GroupProfile
from .models import Post, Event
from django.contrib.auth.models import User
from django.contrib import messages

@login_required
def group_admin(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_profile = getattr(group, 'profile', None)
    # Only the creator can manage admins
    if not group_profile or group_profile.creator != request.user:
        return redirect('group_profile', pk=group.id)
    members = group.user_set.all()
    group_posts = Post.objects.filter(group=group).order_by('-created_at')
    group_events = Event.objects.filter(group=group).order_by('-start_time')
    # Handle admin promotion/demotion
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        if action in ['promote', 'demote'] and user_id:
            user = get_object_or_404(User, id=user_id)
            if user in members:
                if action == 'promote' and user != group_profile.creator:
                    group_profile.admins.add(user)
                    messages.success(request, f"{user.username} promoted to admin.")
                elif action == 'demote' and user != group_profile.creator:
                    group_profile.admins.remove(user)
                    messages.success(request, f"{user.username} demoted from admin.")
            return redirect('group_admin', group_id=group.id)
    return render(request, 'activities/group_admin.html', {
        'group': group,
        'group_profile': group_profile,
        'members': members,
        'group_posts': group_posts,
        'group_events': group_events,
    })
