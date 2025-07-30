from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
from .models import user_profile
from django.shortcuts import render , redirect , get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login , logout , authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from . forms import profileForm, ProfileUpdateForm
from . models import user_profile
from django.contrib.auth.models import Group
from .forms import GroupCreateForm
from .models import GroupProfile
from .forms import GroupProfileForm
from django.http import HttpResponseForbidden, JsonResponse
from .models_group_message import GroupMessage
from django.views.decorators.http import require_POST
from .models_private_message import PrivateMessage
import datetime
from django.db.models import Q
from notifications.utils import create_notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from notifications.utils import send_push_notification_v1
from .models_block_report import UserBlock, UserReport
from .models import user_following

# Create your views here.
@csrf_exempt
@require_POST
@login_required
def save_fcm_token(request):
    token = request.POST.get('token')
    if not token:
        return JsonResponse({'status': 'error', 'message': 'No token provided'}, status=400)
    try:
        profile = user_profile.objects.get(user=request.user)
        profile.fcm_token = token
        profile.save()
        return JsonResponse({'status': 'success'})
    except user_profile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User profile not found'}, status=404)
#=============login view
def login_user(request):
    if request.user.is_authenticated:
        return redirect('activities:home')
    if request.method =='POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        user = authenticate( request , username = username , password =password)
        
        if user is not None :
            login(request , user)
            return redirect('activities:home')  
        else :
            if not User.objects.filter(username=username).exists():
                messages.error(request ,'Username does not exists!')
            else :
                messages.error(request ,'Incorect password')
    return render(request , 'users/login.html')

#=============logout view
@login_required(login_url='/login/')
def logout_user(request):  
    logout(request)   
    return redirect('users:welcome')

#=============registration view
def register_user(request):
    
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user =form.save(commit=False)
            user.username =user.username.lower()
            user.save()
            return redirect('users:login')
        else :
            messages.error(request ,'Registartion failed please try again!')
    return render(request , 'users/register.html' , {'form': form})

#=============profile view
def profile_user(request , pk):
    if pk is None or pk == 'None':
        messages.error(request, 'Invalid user profile requested.')
        return redirect('/')  
    user = get_object_or_404(User , id = pk)
    # Always check if user is a Google user and set username to first name if needed
    
    google_first_name = None
    try:
        from allauth.socialaccount.models import SocialAccount
        social = SocialAccount.objects.filter(user=user, provider='google').first()
        if social and 'given_name' in social.extra_data:
            google_first_name = social.extra_data['given_name']
    except Exception:
        pass
    if google_first_name and (user.username == user.email or user.username == '' or user.username.startswith('user')):
        user.username = google_first_name
        user.save()

    # Ensure a profile exists for the user; if not, create one (for social logins)
    profile_qs = user_profile.objects.filter(user=user)
    if not profile_qs.exists():
        
        # Attempt to autofill email for Google users
        email = user.email
        try:
            from allauth.socialaccount.models import SocialAccount
            social = SocialAccount.objects.filter(user=user, provider='google').first()
            if social and 'email' in social.extra_data:
                email = social.extra_data['email']
        except Exception:
            pass
        # Check if a profile with this email already exists (from another user or previous import)
        
        existing_profile = user_profile.objects.filter(email=email).first()
        if existing_profile:
            # If a profile with this email exists, link it to this user if not already linked
            
            if existing_profile.user != user:
                existing_profile.user = user
                existing_profile.save()
            profile_qs = user_profile.objects.filter(user=user)
        else:
            profile = user_profile.objects.create(user=user, email=email)
            profile_qs = user_profile.objects.filter(user=user)
    profile = profile_qs
    is_following = False
    followers_count = user.followers.count()
    following_count = user.following.count()
    user_groups = user.created_groups.all()  
    
    # Get posts and events created by this user
    from activities.models import Post, Event, Repost, Save
    posts = Post.objects.filter(author=user).order_by('-created_at')
    
    # Show all events created by user (global and group)
    events = Event.objects.filter(creator=user).order_by('-start_time')
    reposts = Repost.objects.filter(user=user).order_by('-created_at')
    saved_posts = Post.objects.filter(saves__user=user).order_by('-created_at').distinct()
    
    # Annotate can_edit/can_delete for template logic
    for post in posts:
        post.can_edit = post.can_edit(request.user)
        post.can_delete = post.can_delete(request.user)
    for event in events:
        event.can_edit = event.can_edit(request.user)
        event.can_delete = event.can_delete(request.user)
    for repost in reposts:
        repost.can_edit = repost.post.can_edit(request.user)
        repost.can_delete = repost.post.can_delete(request.user)
    for post in saved_posts:
        post.can_edit = post.can_edit(request.user)
        post.can_delete = post.can_delete(request.user)
    if request.user.is_authenticated and request.user != user:
        from .models import user_following
        is_following = user_following.objects.filter(user=request.user, following_user=user).exists()
    from django.conf import settings
    context ={
        'user': user ,
        'profile': profile,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'user_groups': user_groups,
        'posts': posts,
        'reposts': reposts,
        'saved_posts': saved_posts,
        'events': events,
        
    }
    return render(request , 'users/profile.html' ,context )

#=========== design profile view
def edit_user(request , pk):
    user = get_object_or_404(User , id = pk)
    try:
        profile = user_profile.objects.get(user=user)
    except user_profile.DoesNotExist:
        messages.error(request, 'Profile does not exist for this user. Please contact admin.')
        return redirect('users:profile', pk=user.id)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Check for unique email
            
            email = form.cleaned_data.get('email')
            if email and user_profile.objects.filter(email=email).exclude(pk=profile.pk).exists():
                form.add_error('email', 'This email is already in use by another profile.')
            else:
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
                # Save first and last name to User model
                
                user.first_name = form.cleaned_data.get('first_name', user.first_name)
                user.last_name = form.cleaned_data.get('last_name', user.last_name)
                user.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('users:profile', pk=user.id)
    else:
        form = ProfileUpdateForm(instance=profile, initial={
            'first_name': user.first_name,
            'last_name': user.last_name
        })
    context ={
        'user': user,
        'form': form
    }
    return render(request , 'users/edit_profile.html' ,context)

#=========== welcome view
def welcome_user(request):
    return render(request , 'users/welcome.html')

#============= Search functionality
def search_users(request):
    from activities.models import Post, Event
    from fellowship.models import FellowshipPost, FellowshipEvent
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(username__icontains=query)
        posts = Post.objects.filter(content__icontains=query)
        events = Event.objects.filter(title__icontains=query)
        fellowship_posts = FellowshipPost.objects.filter(content__icontains=query)
        fellowship_events = FellowshipEvent.objects.filter(title__icontains=query)
    else:
        users = User.objects.all()[:50]
        posts = Post.objects.all().order_by('-created_at')[:20]
        events = Event.objects.all().order_by('-start_time')[:10]
        fellowship_posts = FellowshipPost.objects.all().order_by('-created_at')[:20]
        fellowship_events = FellowshipEvent.objects.all().order_by('-start_time')[:10]
    context = {
        'query': query,
        'users': users,
        'posts': posts,
        'events': events,
        'fellowship_posts': fellowship_posts,
        'fellowship_events': fellowship_events,
    }
    return render(request, 'users/search_results.html', context)

#================= Follow and Unfollow functionality
@login_required
def follow_user(request, pk):
    target_user = get_object_or_404(User, id=pk)
    if request.user != target_user:
        from .models import user_following
        user_following.objects.get_or_create(user=request.user, following_user=target_user)
        from notifications.models import Notification
        from notifications.tasks import send_notification_task
        notification = Notification.objects.create(
            sender=request.user,
            recipient=target_user,
            notification_type='follow',
            message=f'{request.user} started following you.'
        )
                # Push notification
        try:
            profile = user_profile.objects.get(user=target_user)
            if profile.fcm_token:
                send_push_notification_v1(
                    profile.fcm_token,
                    title="New Follower",
                    body=f"{request.user.username} started following you."
                )
        except user_profile.DoesNotExist:
            pass
    return redirect('users:profile', pk=pk)

@login_required
def unfollow_user(request, pk):
    target_user = get_object_or_404(User, id=pk)
    if request.user != target_user:
        
        user_following.objects.filter(user=request.user, following_user=target_user).delete()
    return redirect('users:profile', pk=pk)

#================= Group functionality
@login_required
def create_group(request):
    if request.method == 'POST':
        group_form = GroupCreateForm(request.POST)
        profile_form = GroupProfileForm(request.POST, request.FILES)
        if group_form.is_valid() and profile_form.is_valid():
            group = group_form.save()
            group.user_set.add(request.user)  # Add creator to group
            group_profile = profile_form.save(commit=False)
            group_profile.group = group
            group_profile.creator = request.user
            # Save profile image and description directly on creation
            group_profile.save()
            messages.success(request, 'Group created successfully!')
            return redirect('users:group_profile', pk=group.id)
    else:
        group_form = GroupCreateForm()
        profile_form = GroupProfileForm()
    return render(request, 'users/create_group.html', {'group_form': group_form, 'profile_form': profile_form})

@login_required
def group_list(request):
    groups = Group.objects.all()
    return render(request, 'users/group_list.html', {'groups': groups})

@login_required
def group_profile_view(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group_profile = getattr(group, 'profile', None)
    # Ensure creator is always in admins (fix for legacy groups)
    
    if group_profile and group_profile.creator and group_profile.creator not in group_profile.admins.all():
        group_profile.admins.add(group_profile.creator)
    members = group.user_set.all()
    
    # Show only posts/events for this group
    from activities.models import Post, Event
    group_posts = Post.objects.filter(group=group).order_by('-created_at')
    group_events = Event.objects.filter(group=group).order_by('-start_time')

    # Annotate posts/events with can_edit/can_delete for template logic
    for post in group_posts:
        post.can_edit = post.can_edit(request.user)
        post.can_delete = post.can_delete(request.user)
    for event in group_events:
        event.can_edit = event.can_edit(request.user)
        event.can_delete = event.can_delete(request.user)

    return render(request, 'users/group_profile.html', {
        'group': group,
        'group_profile': group_profile,
        'members': members,
        'group_posts': group_posts,
        'group_events': group_events,
    })

@login_required
def edit_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group_profile = getattr(group, 'profile', None)
    if not group_profile or group_profile.creator != request.user:
        messages.error(request, 'You are not allowed to edit this group.')
        return redirect('users:group_profile', pk=pk)
    if request.method == 'POST':
        form = GroupProfileForm(request.POST, request.FILES, instance=group_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group updated successfully!')
            return redirect('users:group_profile', pk=pk)
    else:
        form = GroupProfileForm(instance=group_profile)
    return render(request, 'users/edit_group.html', {'form': form, 'group': group})

@login_required
def join_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.user not in group.user_set.all():
        group.user_set.add(request.user)
        messages.success(request, f'You joined {group.name}!')

@login_required
def leave_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.user in group.user_set.all():
        
        # Prevent creator from leaving their own group
        if hasattr(group, 'profile') and group.profile.creator == request.user:
            messages.error(request, 'Creators cannot leave their own group.')
            return redirect('users:group_profile', pk=pk)
        group.user_set.remove(request.user)
        messages.success(request, f'You left {group.name}.')
    return redirect('users:group_profile', pk=pk)

@login_required
def group_chat(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.user not in group.user_set.all():
        return HttpResponseForbidden('You must be a member to view the chat.')
    messages_qs = GroupMessage.objects.filter(group=group).select_related('user').prefetch_related('reactions').order_by('timestamp')
    emojis = ['👍', '❤️', '😂']
    
    # Annotate each message with reaction counts, user's own reaction, and tuples for template
    for msg in messages_qs:
        reaction_counts = {emoji: 0 for emoji in emojis}
        user_reaction = None
        for reaction in msg.reactions.all():
            if reaction.emoji in reaction_counts:
                reaction_counts[reaction.emoji] += 1
            if reaction.user == request.user:
                user_reaction = reaction.emoji
        msg.reaction_counts = reaction_counts
        msg.user_reaction = user_reaction
        msg.reaction_tuples = [(emoji, reaction_counts[emoji]) for emoji in emojis]
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        file = request.FILES.get('file')
        if content:
            from users.models_group_message import GroupMessage
            from notifications.models import Notification
            from notifications.tasks import send_notification_task
            msg = GroupMessage.objects.create(group=group, user=request.user, content=content, file=file)
            
            # Notify all group members except sender
            members = group.user_set.exclude(id=request.user.id)
            for member in members:
                notification = Notification.objects.create(
                    sender=request.user,
                    recipient=member,
                    notification_type='message',
                    message=f'New group message from {request.user.username} in {group.name}.'
                )
        if content or file:
            msg = GroupMessage.objects.create(group=group, user=request.user, content=content, file=file)
            
            # Real-time WebSocket broadcast to group
            channel_layer = get_channel_layer()
            group_name = f"group_{group.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_group_message",
                    "message": {
                        "sender": str(request.user),
                        "content": content,
                        "timestamp": str(msg.timestamp),
                        "id": msg.id
                    }
                }
            )
            # Notify all group members except sender
            
            for member in group.user_set.exclude(id=request.user.id):
                create_notification(
                    sender=request.user,
                    recipient=member,
                    notification_type='message',
                    message=f'New group message in {group.name}: {content[:50]}',
                    related_object=msg
                )
            # push notifications for group
            members = group.user_set.exclude(id=request.user.id)
            for member in members:
                try:
                    profile = user_profile.objects.get(user=member)
                    if profile.fcm_token:
                        send_push_notification_v1(
                            profile.fcm_token,
                            title="New Group Message",
                            body=f"{request.user.username} in {group.name}: {content[:50]}"
                        )
                except user_profile.DoesNotExist:
                    pass
    return render(request, 'users/group_chat.html', {'group': group, 'messages': messages_qs, 'emojis': emojis})

@login_required
def edit_group_message(request, msg_id):
    from .models_group_message import GroupMessage
    msg = get_object_or_404(GroupMessage, id=msg_id)
    if msg.user != request.user:
        return HttpResponseForbidden('You can only edit your own messages.')
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg.content = content
            msg.save()
            return redirect('users:group_chat', pk=msg.group.id)
    return render(request, 'users/edit_group_message.html', {'msg': msg})

@login_required
@require_POST
def delete_group_message(request, msg_id):
    from .models_group_message import GroupMessage
    msg = get_object_or_404(GroupMessage, id=msg_id)
    group_id = msg.group.id
    if msg.user == request.user:
        msg.delete()
        messages.success(request, 'Message deleted.')
    else:
        return HttpResponseForbidden('You can only delete your own messages.')
    return redirect('users:group_chat', pk=group_id)

@login_required
def react_to_message(request, msg_id, emoji):
    from .models_group_message import GroupMessage
    from .models_group_reaction import GroupMessageReaction
    msg = get_object_or_404(GroupMessage, id=msg_id)
    # Remove any previous reaction by this user for this 
    
    GroupMessageReaction.objects.filter(message=msg, user=request.user).delete()
    # Add the new reaction
    
    GroupMessageReaction.objects.create(message=msg, user=request.user, emoji=emoji)
    return redirect('users:group_chat', pk=msg.group.id)

@login_required
def pin_message(request, msg_id):
    from .models_group_message import GroupMessage
    msg = get_object_or_404(GroupMessage, id=msg_id)
    group_profile = getattr(msg.group, 'profile', None)
    if group_profile and request.user == group_profile.creator:
        msg.pinned = True
        msg.save()
    return redirect('users:group_chat', pk=msg.group.id)

@login_required
def unpin_message(request, msg_id):
    from .models_group_message import GroupMessage
    msg = get_object_or_404(GroupMessage, id=msg_id)
    group_profile = getattr(msg.group, 'profile', None)
    if group_profile and request.user == group_profile.creator:
        msg.pinned = False
        msg.save()
    return redirect('users:group_chat', pk=msg.group.id)

@login_required
def analytics_dashboard(request):
    from activities.models import Post, Event
    from .models import user_following
    user_id = request.GET.get('user_id')
    if user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user
    # User stats
    
    post_count = Post.objects.filter(author=user).count()
    event_count = Event.objects.filter(creator=user).count()
    followers_count = user.followers.count() if hasattr(user, 'followers') else 0
    following_count = user.following.count() if hasattr(user, 'following') else 0
    # Screentime: sum of time between first and last activity (proxy)
    
    post_times = Post.objects.filter(author=user).values_list('created_at', flat=True)
    event_times = Event.objects.filter(creator=user).values_list('start_time', flat=True)
    all_times = list(post_times) + list(event_times)
    if all_times:
        earliest = min(all_times)
        latest = max(all_times)
        screentime_seconds = (latest - earliest).total_seconds()
        screentime = str(datetime.timedelta(seconds=int(screentime_seconds)))
    else:
        screentime = '0:00:00'
    # Group stats (for groups the user is an admin of)
    
    group_stats = []
    if hasattr(user, 'admin_groups'):
        for group_profile in user.admin_groups.all():
            group = group_profile.group
            group_post_count = Post.objects.filter(group=group).count()
            group_event_count = Event.objects.filter(group=group).count()
            group_member_count = group.user_set.count()
            group_stats.append({
                'name': group.name,
                'posts': group_post_count,
                'events': group_event_count,
                'members': group_member_count,
            })
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'user': {
                'posts': post_count,
                'events': event_count,
                'followers': followers_count,
                'following': following_count,
                'screentime': screentime,
            },
            'groups': group_stats,
        })
    return render(request, 'users/analytics_dashboard.html', {'profile_user': user})

@login_required
def private_messages(request, user_id=None):
    from .models import user_following
    # Only show users the current user follows
    
    following_ids = user_following.objects.filter(user=request.user).values_list('following_user', flat=True)
    users = User.objects.filter(id__in=following_ids)
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query)
    other_user = None
    if user_id:
        other_user = get_object_or_404(User, id=user_id)
    # Unread message counts for each user
    
    from .models_private_message import PrivateMessage
    unread_counts = {}
    for u in users:
        unread_counts[u.id] = PrivateMessage.objects.filter(
            sender=u, recipient=request.user, is_read=False
        ).count()
    # Filter messages for latest sent/received
    
    if other_user:
        messages_qs = PrivateMessage.objects.filter(
            (Q(sender=request.user) & Q(recipient=other_user)) |
            (Q(sender=other_user) & Q(recipient=request.user))
        ).order_by('created_at')
        # Mark all messages from other_user as read
        
        PrivateMessage.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    else:
        messages_qs = []
    from django.db.models import Max
    latest_msgs = PrivateMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).values('sender', 'recipient').annotate(latest=Max('created_at'))
    latest_user_ids = set()
    for entry in latest_msgs:
        if entry['sender'] == request.user.id:
            latest_user_ids.add(entry['recipient'])
        else:
            latest_user_ids.add(entry['sender'])
    users = users.annotate(
        last_msg=Max(
            'sent_messages__created_at',
            filter=Q(sent_messages__recipient=request.user)
        )
    ).order_by('-last_msg')
    if request.method == 'POST' and other_user:
        content = request.POST.get('content', '')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        file = request.FILES.get('file')
        if content or image or video or file:
            msg = PrivateMessage.objects.create(
                sender=request.user,
                recipient=other_user,
                content=content,
                image=image,
                video=video,
                file=file,
                is_read=False
            )
            # Real-time WebSocket broadcast
            
            channel_layer = get_channel_layer()
            group_name = f"private_{other_user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_private_message",
                    "message": {
                        "sender": str(request.user),
                        "content": content,
                        "timestamp": str(msg.created_at),
                        "id": msg.id
                    }
                }
            )
            create_notification(
                sender=request.user,
                recipient=other_user,
                notification_type='message',
                message=content or 'You have a new message',
                related_object=msg
            )
            try:
                profile = user_profile.objects.get(user=other_user)
                print("DEBUG: FCM token for", other_user.username, "=", profile.fcm_token)
                if profile.fcm_token:
                    send_push_notification_v1(
                        profile.fcm_token,
                        title="New Message",
                        body=f"{request.user.username}: {content[:50]}"
                    )
                    print("DEBUG: Sent push notification to", other_user.username)
            except user_profile.DoesNotExist:
                print("DEBUG: No user_profile for", other_user.username)
            
    return render(request, 'users/private_messages.html', {
        'other_user': other_user,
        'messages': messages_qs,
        'users': users,
        'search_query': search_query,
        'unread_counts': unread_counts,
    })

@login_required
def user_settings(request):
    return render(request, 'users/settings.html', {'user': request.user})

@login_required
def group_admin(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group_profile = getattr(group, 'profile', None)
    if not group_profile or request.user not in group_profile.admins.all():
        messages.error(request, 'You are not allowed to access the group admin panel.')
        return redirect('users:group_profile', pk=pk)
    members = group.user_set.all()
    from activities.models import Post
    group_posts = Post.objects.filter(group=group).order_by('-created_at')
    return render(request, 'users/group_admin.html', {
        'group': group,
        'group_profile': group_profile,
        'members': members,
        'group_posts': group_posts,
    })

#=========== create user profile view

@login_required
def create_user_profile(request, pk):
    user = get_object_or_404(User, id=pk)
    # Prevent duplicate profile creation
    
    if user_profile.objects.filter(user=user).exists():
        messages.info(request, 'Profile already exists for this user.')
        return redirect('users:edit_user', pk=user.id)
    from django.db import transaction
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES)
        email = form.data.get('email', '').strip().lower()
        if email and user_profile.objects.filter(email__iexact=email).exists():
            form.add_error('email', 'This email is already in use by another profile.')
        try:
            with transaction.atomic():
                profile = form.save(commit=False)
                profile.user = user 
                if form.is_valid():
                    # Always update User model fields from form
                    
                    user.username = form.cleaned_data.get('username', user.username)
                    user.first_name = form.cleaned_data.get('first_name', user.first_name)
                    user.last_name = form.cleaned_data.get('last_name', user.last_name)
                    user.email = form.cleaned_data.get('email', user.email)
                    user.save()
                    profile.email = user.email
                    profile.save()
                    
                    # Refresh user session to reflect changes everywhere
                    if request.user.id == user.id:
                        from django.contrib.auth import update_session_auth_hash
                        update_session_auth_hash(request, user)
                    messages.success(request, 'Profile created successfully!')
                    return redirect('users:profile', pk=user.id)
                else:       
                    pass
        except Exception as e:
            form.add_error(None, f'Error creating profile: {str(e)}')
    else:
        initial = {}
        try:
            from allauth.socialaccount.models import SocialAccount
            social = SocialAccount.objects.filter(user=user, provider='google').first()
            if social and 'email' in social.extra_data:
                initial['email'] = social.extra_data['email']
        except Exception:
            pass
        form = ProfileUpdateForm(initial=initial)
    context = {
        'user': user,
        'form': form
    }
    return render(request, 'users/create_profile.html', context)

@csrf_exempt
@login_required
def mark_messages_read(request, user_id):
    if request.method == 'POST':
        from .models_private_message import PrivateMessage
        PrivateMessage.objects.filter(sender_id=user_id, recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'invalid'}, status=400)

@csrf_exempt
@login_required
def mark_group_messages_read(request, group_id):
    if request.method == 'POST':
        from .models_group_message import GroupMessage
        GroupMessage.objects.filter(group_id=group_id, is_read=False).exclude(user=request.user).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'invalid'}, status=400)

@login_required
def block_user(request, pk):
    target = get_object_or_404(User, id=pk)
    if target != request.user:
        UserBlock.objects.get_or_create(blocker=request.user, blocked=target)
        messages.success(request, f'You have blocked {target.username}.')
    return redirect('users:profile', pk=pk)

@login_required
def report_user(request, pk):
    target = get_object_or_404(User, id=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if reason:
            UserReport.objects.create(reporter=request.user, reported=target, reason=reason)
            messages.success(request, f'You have reported {target.username}.')
            return redirect('users:profile', pk=pk)
    return render(request, 'users/report_user.html', {'target': target})

@login_required
def edit_privacy(request):
    profile = request.user.profile
    if request.method == 'POST':
        privacy = request.POST.get('privacy')
        if privacy in dict(profile.PRIVACY_CHOICES):
            profile.privacy = privacy
            profile.save()
            messages.success(request, 'Privacy settings updated.')
            return redirect('users:profile', pk=request.user.id)
    return render(request, 'users/edit_privacy.html', {'profile': profile})

@login_required
def friend_suggestions(request):
    
    # Suggest users not already followed, not self, not blocked
    following_ids = request.user.following.values_list('following_user_id', flat=True)
    blocked_ids = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
    suggestions = User.objects.exclude(id__in=list(following_ids) + [request.user.id] + list(blocked_ids))[:10]
    return render(request, 'users/friend_suggestions.html', {'suggestions': suggestions})

@login_required
def advanced_search(request):
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    group = request.GET.get('group', '')
    users = User.objects.all()
    if query:
        users = users.filter(username__icontains=query)
    if location:
        users = users.filter(profile__location__icontains=location)
    if group:
        users = users.filter(created_groups__name__icontains=group)
    users = users.distinct()[:20]
    return render(request, 'users/advanced_search.html', {'users': users, 'query': query, 'location': location, 'group': group})