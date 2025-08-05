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
from django.db.models import Q, Count, Max, Prefetch
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
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import transaction

# Create your views here.
@csrf_exempt
@require_POST
@login_required
def save_fcm_token(request):
    token = request.POST.get('token')
    if not token:
        return JsonResponse({'status': 'error', 'message': 'No token provided'}, status=400)
    try:
        # Use update_or_create to avoid race conditions
        profile, created = user_profile.objects.update_or_create(
            user=request.user,
            defaults={'fcm_token': token}
        )
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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
            # Use exists() instead of filter() for better performance
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
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            return redirect('users:login')
        else :
            messages.error(request ,'Registartion failed please try again!')
    return render(request , 'users/register.html' , {'form': form})

#=============profile view - HEAVILY OPTIMIZED
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.models import User
from users.models import user_profile, user_following
from django.db.models import Count, Q
from allauth.socialaccount.models import SocialAccount
from activities.models import Post, Event, Repost
from django.conf import settings

def profile_user(request, pk):
    if pk is None or pk == 'None':
        messages.error(request, 'Invalid user profile requested.')
        return redirect('/')

    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('/')

    # Cache profile only
    cache_key = f'user_profile_setup_{pk}'
    profile = cache.get(cache_key)

    if not profile:
        # Check Google Social Account for name and email
        google_first_name = None
        email = user.email

        try:
            social = SocialAccount.objects.filter(user=user, provider='google').first()
            if social:
                google_first_name = social.extra_data.get('given_name')
                email = social.extra_data.get('email', email)
        except Exception:
            pass

        # Set username from Google first name if needed
        if google_first_name and (user.username == user.email or user.username == '' or user.username.startswith('user')):
            user.username = google_first_name
            user.save()

        # Fetch or create profile
        existing_profile = user_profile.objects.filter(email=email).first()
        if existing_profile:
            if existing_profile.user != user:
                existing_profile.user = user
                existing_profile.save()
            profile = existing_profile
        else:
            profile, _ = user_profile.objects.get_or_create(
                user=user,
                defaults={'email': email}
            )

        # Cache for 5 minutes
        cache.set(cache_key, profile, 300)

    # Accurate follower and following counts
    followers_count = user_following.objects.filter(following_user=user).count()
    following_count = user_following.objects.filter(user=user).count()

    # Following status (is request.user following this user?)
    is_following = False
    if request.user.is_authenticated and request.user != user:
        is_following = user_following.objects.filter(
            user=request.user,
            following_user=user
        ).exists()

    # Posts, events, reposts, saved posts
    posts = Post.objects.filter(author=user).select_related('author').order_by('-created_at')[:20]
    events = Event.objects.filter(creator=user).select_related('creator').order_by('-start_time')[:10]
    reposts = Repost.objects.filter(user=user).select_related('user', 'post__author').order_by('-created_at')[:10]
    saved_posts = Post.objects.filter(saves__user=user).select_related('author').order_by('-created_at').distinct()[:10]

    # Groups
    user_groups = user.created_groups.all()[:10]

    # Permissions
    for post in posts:
        post.can_edit = post.author == request.user
        post.can_delete = post.author == request.user

    for event in events:
        event.can_edit = event.creator == request.user
        event.can_delete = event.creator == request.user

    for repost in reposts:
        repost.can_edit = repost.post.author == request.user
        repost.can_delete = repost.post.author == request.user

    for post in saved_posts:
        post.can_edit = post.author == request.user
        post.can_delete = post.author == request.user

    context = {
        'user': user,
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
    return render(request, 'users/profile.html', context)

#=========== design profile view - OPTIMIZED
def edit_user(request, pk):
    # Use select_related to avoid additional query
    user = get_object_or_404(User.objects.select_related(), id=pk)
    
    try:
        profile = user_profile.objects.get(user=user)
    except user_profile.DoesNotExist:
        messages.error(request, 'Profile does not exist for this user. Please contact admin.')
        return redirect('users:profile', pk=user.id)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            # More efficient uniqueness check
            if email and user_profile.objects.filter(email=email).exclude(pk=profile.pk).exists():
                form.add_error('email', 'This email is already in use by another profile.')
            else:
                # Use transaction for atomicity
                with transaction.atomic():
                    profile = form.save(commit=False)
                    profile.user = user
                    profile.save()
                    
                    user.first_name = form.cleaned_data.get('first_name', user.first_name)
                    user.last_name = form.cleaned_data.get('last_name', user.last_name)
                    user.save()
                    
                    # Clear cache after update
                    cache.delete(f'user_profile_setup_{pk}')
                    
                messages.success(request, 'Profile updated successfully!')
                return redirect('users:profile', pk=user.id)
    else:
        form = ProfileUpdateForm(instance=profile, initial={
            'first_name': user.first_name,
            'last_name': user.last_name
        })
    
    context = {
        'user': user,
        'form': form
    }
    return render(request, 'users/edit_profile.html', context)

#=========== welcome view
def welcome_user(request):
    if request.user.is_authenticated:
        return redirect('activities:home')
    else:
        return render(request, 'users/welcome.html')

#============= Search functionality - OPTIMIZED
def search_users(request):
    from activities.models import Post, Event
    from fellowship.models import FellowshipPost, FellowshipEvent
    
    query = request.GET.get('q', '').strip()
    
    if query:
        # Use select_related and limit results for performance
        users = User.objects.filter(username__icontains=query).select_related()[:20]
        posts = Post.objects.filter(content__icontains=query).select_related('author')[:15]
        events = Event.objects.filter(title__icontains=query).select_related('creator')[:10]
        fellowship_posts = FellowshipPost.objects.filter(content__icontains=query).select_related('author')[:15]
        fellowship_events = FellowshipEvent.objects.filter(title__icontains=query).select_related('creator')[:10]
    else:
        # Limit results when no query to avoid large datasets
        users = User.objects.select_related().order_by('-date_joined')[:20]
        posts = Post.objects.select_related('author').order_by('-created_at')[:15]
        events = Event.objects.select_related('creator').order_by('-start_time')[:8]
        fellowship_posts = FellowshipPost.objects.select_related('author').order_by('-created_at')[:15]
        fellowship_events = FellowshipEvent.objects.select_related('creator').order_by('-start_time')[:8]
    
    context = {
        'query': query,
        'users': users,
        'posts': posts,
        'events': events,
        'fellowship_posts': fellowship_posts,
        'fellowship_events': fellowship_events,
    }
    return render(request, 'users/search_results.html', context)

#================= Follow and Unfollow functionality - OPTIMIZED
@login_required
def follow_user(request, pk):
    target_user = get_object_or_404(User, id=pk)
    if request.user != target_user:
        # Use get_or_create to avoid race conditions
        follow_obj, created = user_following.objects.get_or_create(
            user=request.user, 
            following_user=target_user
        )
        
        if created:  # Only create notification if it's a new follow
            from notifications.models import Notification
            notification = Notification.objects.create(
                sender=request.user,
                recipient=target_user,
                notification_type='follow',
                message=f'{request.user} started following you.'
            )
            
            # Push notification - use try/except for error handling
            try:
                profile = user_profile.objects.select_related('user').get(user=target_user)
                if profile.fcm_token:
                    send_push_notification_v1(
                        profile.fcm_token,
                        title="New Follower",
                        body=f"{request.user.username} started following you."
                    )
            except user_profile.DoesNotExist:
                pass
            
        # Clear relevant caches
        cache.delete(f'user_profile_setup_{pk}')
        
    return redirect('users:profile', pk=pk)

@login_required
def unfollow_user(request, pk):
    target_user = get_object_or_404(User, id=pk)
    if request.user != target_user:
        # Use filter().delete() for efficiency
        deleted_count = user_following.objects.filter(
            user=request.user, 
            following_user=target_user
        ).delete()[0]
        
        # Clear cache if unfollow happened
        if deleted_count > 0:
            cache.delete(f'user_profile_setup_{pk}')
            
    return redirect('users:profile', pk=pk)

#================= Group functionality - OPTIMIZED
@login_required
def create_group(request):
    if request.method == 'POST':
        group_form = GroupCreateForm(request.POST)
        profile_form = GroupProfileForm(request.POST, request.FILES)
        
        if group_form.is_valid() and profile_form.is_valid():
            # Use transaction for atomicity
            with transaction.atomic():
                group = group_form.save()
                group.user_set.add(request.user)
                
                group_profile = profile_form.save(commit=False)
                group_profile.group = group
                group_profile.creator = request.user
                group_profile.save()
                
            messages.success(request, 'Group created successfully!')
            return redirect('users:group_profile', pk=group.id)
    else:
        group_form = GroupCreateForm()
        profile_form = GroupProfileForm()
        
    return render(request, 'users/create_group.html', {
        'group_form': group_form, 
        'profile_form': profile_form
    })

@login_required
def group_list(request):
    # Add pagination or limit results for performance
    groups = Group.objects.select_related('profile').annotate(
        member_count=Count('user')
    ).order_by('-id')[:50]
    
    return render(request, 'users/group_list.html', {'groups': groups})

@login_required
def group_profile_view(request, pk):
    # Use select_related and prefetch_related for efficiency
    group = get_object_or_404(
        Group.objects.select_related('profile').prefetch_related('user_set'),
        pk=pk
    )
    
    group_profile = getattr(group, 'profile', None)
    
    # Ensure creator is in admins
    if group_profile and group_profile.creator and group_profile.creator not in group_profile.admins.all():
        group_profile.admins.add(group_profile.creator)

    members = group.user_set.all()

    # Optimize content queries
    from activities.models import Post, Event
    group_posts = Post.objects.filter(group=group).select_related('author').order_by('-created_at')[:20]
    group_events = Event.objects.filter(group=group).select_related('creator').order_by('-start_time')[:10]

    # Pre-calculate permissions
    for post in group_posts:
        post.can_edit = post.author == request.user
        post.can_delete = post.author == request.user
        
    for event in group_events:
        event.can_edit = event.creator == request.user
        event.can_delete = event.creator == request.user

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
    return redirect('users:group_profile', pk=pk)

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
    
    # Check membership efficiently
    if not group.user_set.filter(id=request.user.id).exists():
        return HttpResponseForbidden('You must be a member to view the chat.')
    
    # Optimize message loading with pagination
    messages_qs = GroupMessage.objects.filter(...)
    
    emojis = ['👍', '❤️', '😂']
    
    # Batch process reactions to avoid N+1 queries
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
        
        if content or file:
            msg = GroupMessage.objects.create(
                group=group, 
                user=request.user, 
                content=content, 
                file=file
            )
            
            # WebSocket broadcast
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
            
            # Bulk create notifications and push notifications
            members = group.user_set.exclude(id=request.user.id)
            
            # Create notifications
            for member in members:
                create_notification(
                    sender=request.user,
                    recipient=member,
                    notification_type='message',
                    message=f'New group message in {group.name}: {content[:50]}',
                    related_object=msg
                )
            
            # Send push notifications
            member_profiles = user_profile.objects.filter(
                user__in=members
            ).exclude(fcm_token__isnull=True).exclude(fcm_token='')
            
            for profile in member_profiles:
                try:
                    send_push_notification_v1(
                        profile.fcm_token,
                        title="New Group Message",
                        body=f"{request.user.username} in {group.name}: {content[:50]}"
                    )
                except Exception:
                    pass

    return render(request, 'users/group_chat.html', {
        'group': group, 
        'messages': messages_qs, 
        'emojis': emojis
    })

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
    
    # Remove any previous reaction by this user for this message
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
    
    user_id = request.GET.get('user_id')
    if user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user

    # User stats - Use annotations for efficiency
    user_stats = User.objects.filter(id=user.id).annotate(
        post_count=Count('post_set'),
        event_count=Count('event_set'),
        followers_count=Count('followers'),
        following_count=Count('following')
    ).first()

    post_count = user_stats.post_count if user_stats else 0
    event_count = user_stats.event_count if user_stats else 0
    followers_count = user_stats.followers_count if user_stats else 0
    following_count = user_stats.following_count if user_stats else 0

    # Screentime calculation - optimized with values_list
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

    # Group stats (optimized)
    group_stats = []
    if hasattr(user, 'admin_groups'):
        admin_groups = user.admin_groups.select_related('group').prefetch_related(
            Prefetch('group__post_set', queryset=Post.objects.all()),
            Prefetch('group__event_set', queryset=Event.objects.all())
        )
        
        for group_profile in admin_groups:
            group = group_profile.group
            group_stats.append({
                'name': group.name,
                'posts': group.post_set.count(),
                'events': group.event_set.count(),
                'members': group.user_set.count(),
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
    # Optimize following users query
    following_ids = user_following.objects.filter(user=request.user).values_list('following_user', flat=True)
    users = User.objects.filter(id__in=following_ids).select_related()
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query)

    other_user = None
    if user_id:
        other_user = get_object_or_404(User, id=user_id)

    # Optimize unread counts with single query
    from .models_private_message import PrivateMessage
    unread_counts = dict(
        PrivateMessage.objects.filter(
            sender__in=users,
            recipient=request.user,
            is_read=False
        ).values('sender').annotate(count=Count('id')).values_list('sender', 'count')
    )

    # Get messages efficiently
    if other_user:
        messages_qs = PrivateMessage.objects.filter(
            (Q(sender=request.user) & Q(recipient=other_user)) |
            (Q(sender=other_user) & Q(recipient=request.user))
        ).select_related('sender', 'recipient').order_by('created_at')
        
        # Mark messages as read
        PrivateMessage.objects.filter(
            sender=other_user, 
            recipient=request.user, 
            is_read=False
        ).update(is_read=True)
    else:
        messages_qs = []

    # Optimize user ordering
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
            
            # WebSocket and notifications
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
            
            # Push notification
            try:
                profile = user_profile.objects.get(user=other_user)
                if profile.fcm_token:
                    send_push_notification_v1(
                        profile.fcm_token,
                        title="New Message",
                        body=f"{request.user.username}: {content[:50]}"
                    )
            except user_profile.DoesNotExist:
                pass

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
        
    # Optimize queries
    members = group.user_set.select_related().all()
    
    from activities.models import Post
    group_posts = Post.objects.filter(group=group).select_related('author').order_by('-created_at')[:20]
    
    return render(request, 'users/group_admin.html', {
        'group': group,
        'group_profile': group_profile,
        'members': members,
        'group_posts': group_posts,
    })

#=========== create user profile view - OPTIMIZED
@login_required
def create_user_profile(request, pk):
    user = get_object_or_404(User, id=pk)
    
    # Prevent duplicate profile creation
    if user_profile.objects.filter(user=user).exists():
        messages.info(request, 'Profile already exists for this user.')
        return redirect('users:edit_user', pk=user.id)
        
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES)
        email = form.data.get('email', '').strip().lower()
        
        if email and user_profile.objects.filter(email__iexact=email).exists():
            form.add_error('email', 'This email is already in use by another profile.')
            
        if form.is_valid():
            try:
                with transaction.atomic():
                    profile = form.save(commit=False)
                    profile.user = user 
                    
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
        PrivateMessage.objects.filter(
            sender_id=user_id, 
            recipient=request.user, 
            is_read=False
        ).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'invalid'}, status=400)

@csrf_exempt
@login_required
def mark_group_messages_read(request, group_id):
    if request.method == 'POST':
        from .models_group_message import GroupMessage
        GroupMessage.objects.filter(
            group_id=group_id, 
            is_read=False
        ).exclude(user=request.user).update(is_read=True)
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
            UserReport.objects.create(
                reporter=request.user, 
                reported=target, 
                reason=reason
            )
            messages.success(request, f'You have reported {target.username}.')
            return redirect('users:profile', pk=pk)
            
    return render(request, 'users/report_user.html', {'target': target})

@login_required
def edit_privacy(request):
    try:
        profile = request.user.profile
    except AttributeError:
        # Handle case where profile doesn't exist
        profile, created = user_profile.objects.get_or_create(user=request.user)
        
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
    
    suggestions = User.objects.exclude(
        id__in=list(following_ids) + [request.user.id] + list(blocked_ids)
    ).select_related().order_by('?')[:10]  # Random order
    
    return render(request, 'users/friend_suggestions.html', {'suggestions': suggestions})

@login_required
def advanced_search(request):
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    group = request.GET.get('group', '')
    
    users = User.objects.select_related()
    
    if query:
        users = users.filter(username__icontains=query)
    if location:
        users = users.filter(profile__location__icontains=location)
    if group:
        users = users.filter(created_groups__name__icontains=group)
        
    users = users.distinct()[:20]
    
    return render(request, 'users/advanced_search.html', {
        'users': users, 
        'query': query, 
        'location': location, 
        'group': group
    })