import asyncio
import logging
import random
from functools import wraps
from itertools import cycle

from django.template.loader import render_to_string
from asgiref.sync import sync_to_async
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from notifications.utils import create_notification, send_push_notification_v1

from .forms import PostForm, EventForm, CommentForm
from .models import Post, Event, Comment, Like, Save, Share, Repost
from utils.mentions import extract_mentions

logger = logging.getLogger(__name__)

# ======================
# UTILITY FUNCTIONS
# ======================

def async_view(view_func):
    """Decorator to convert sync views to async"""
    @wraps(view_func)
    async def wrapped_view(request, *args, **kwargs):
        return await sync_to_async(view_func)(request, *args, **kwargs)
    return wrapped_view

def cache_key_generator(view_name, request):
    """Generate consistent cache keys"""
    user_id = request.user.id if request.user.is_authenticated else 'anon'
    params = request.GET.urlencode()
    return f"{view_name}_{user_id}_{params}"

async def get_suggested_users(request):
    """Get cached suggested users or generate new suggestions"""
    if not request.user.is_authenticated:
        return []
    
    cache_key = f"suggestions_{request.user.id}"
    suggested_users = await sync_to_async(cache.get)(cache_key, [])
    
    if not suggested_users:
        excluded_ids = [request.user.id] + list(await sync_to_async(list)(
            request.user.following.values_list('following_user', flat=True)
        ))
        suggested_users = list(await sync_to_async(list)(
            User.objects.exclude(id__in=excluded_ids)
            .order_by('?')[:10]
            .select_related('profile')
        ))
        await sync_to_async(cache.set)(cache_key, suggested_users, 3600)
    
    return suggested_users

async def get_suggested_groups():
    """Get cached suggested groups"""
    cache_key = 'suggested_groups'
    suggested_groups = await sync_to_async(cache.get)(cache_key, [])
    
    if not suggested_groups:
        suggested_groups = list(await sync_to_async(list)(
            Group.objects.all().order_by('?')[:10]
        ))
        await sync_to_async(cache.set)(cache_key, suggested_groups, 3600)
    
    return suggested_groups

# ======================
# CORE VIEWS
# ======================

async def home_activities(request):
    """Optimized home feed view with async support"""
    cache_key = cache_key_generator('home_feed', request)
    cached_response = await sync_to_async(cache.get)(cache_key)
    
    if cached_response:
        return cached_response

    # Async data fetching
    base_posts_query = Post.objects.filter(group__isnull=True)\
        .select_related('author', 'group')\
        .prefetch_related('likes', 'comments__author')
    
    base_events_query = Event.objects.filter(group__isnull=True, start_time__gte=timezone.now())\
        .select_related('creator', 'group')\
        .annotate(num_attendees=Count('attendees'))\
        .order_by('-num_attendees', 'start_time')[:10]

    # Execute queries in parallel
    posts, events = await asyncio.gather(
        sync_to_async(list)(base_posts_query),
        sync_to_async(list)(base_events_query)
    )

    # Following filter
    if request.user.is_authenticated and request.GET.get('following') == '1':
        following_ids = await sync_to_async(list)(request.user.following.values_list('following_user', flat=True))
        posts = [p for p in posts if p.author.id in following_ids]
        events = [e for e in events if e.creator.id in following_ids]

    # Search logic
    query = request.GET.get('q', '')
    if query:
        query_lower = query.lower()
        posts = [p for p in posts if 
                query_lower in p.content.lower() or 
                query_lower in p.author.username.lower()]
        events = [e for e in events if 
                 query_lower in e.title.lower() or 
                 query_lower in e.description.lower() or
                 query_lower in e.creator.username.lower()]

    # Get suggestions
    suggested_users, suggested_groups = await asyncio.gather(
        get_suggested_users(request),
        get_suggested_groups()
    )

    # Feed combination
    combined_feed = []
    
    # Add discovery items first
    if suggested_users:
        combined_feed.append(('users_batch', suggested_users[:3]))
    if suggested_groups:
        combined_feed.append(('groups_batch', suggested_groups[:3]))
    if events:
        combined_feed.append(('events', events[0]))

    # Add posts
    combined_feed.extend([('post', post) for post in posts])

    # Batch processing for infinite scroll
    batch_size = 10
    start = int(request.GET.get('start', 0))
    end = start + batch_size
    feed_batch = combined_feed[start:end]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        items_html = []
        for item_type, item in feed_batch:
            items_html.append(await sync_to_async(render_to_string)(
                'activities/_feed_item.html', 
                {'item_type': item_type, 'item': item, 'user': request.user}
            ))
        has_more = end < len(combined_feed)
        return JsonResponse({'items': items_html, 'has_more': has_more})

    context = {
        'combined_feed': combined_feed[:batch_size],
        'query': query,
        'suggested_users': suggested_users,
        'suggested_groups': suggested_groups,
        'events': events,
    }
    
    response = await sync_to_async(render)(request, 'activities/home_feed.html', context)
    await sync_to_async(cache.set)(cache_key, response, 300)
    return response

def group_activities(request): 
    return render(request, 'activities/group_detail.html')

# ======================
# POST/EVENT CRUD VIEWS
# ======================

@login_required
@transaction.atomic
def create_post(request, group_id=None):
    group = None
    if group_id:
        group = get_object_or_404(Group.objects.select_related('profile'), id=group_id)
        if not group.user_set.filter(id=request.user.id).exists():
            return redirect('group_list')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user, group=group)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if group:
                post.group = group
            post.save()

            # Process mentions
            mentioned_usernames = extract_mentions(post.content)
            if mentioned_usernames:
                mentioned_users = User.objects.filter(
                    username__in=mentioned_usernames
                ).exclude(id=request.user.id).select_related('profile')
                
                for user in mentioned_users:
                    create_notification(
                        sender=request.user,
                        recipient=user,
                        notification_type='mention',
                        message=f'You were mentioned by @{request.user.username}',
                        related_object=post
                    )
                    if hasattr(user, 'profile') and user.profile.fcm_token:
                        send_push_notification_v1(
                            user.profile.fcm_token,
                            title="Mention",
                            body=f"You were mentioned by @{request.user.username}"
                        )

            cache.delete_pattern('home_feed_*')
            return redirect('group_profile', pk=group.id) if group else redirect('users:profile', pk=request.user.id)
    else:
        form = PostForm(user=request.user, group=group)

    return render(request, 'activities/create_post.html', {
        'form': form,
        'group': group
    })

@login_required
@transaction.atomic
def create_event(request, group_id=None):
    group = None
    if group_id:
        group = get_object_or_404(Group.objects.select_related('profile'), id=group_id)
        if not group.user_set.filter(id=request.user.id).exists():
            return redirect('group_list')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            if group:
                event.group = group
            event.save()

            # Process mentions
            mentioned_usernames = extract_mentions(event.description)
            if mentioned_usernames:
                mentioned_users = User.objects.filter(
                    username__in=mentioned_usernames
                ).exclude(id=request.user.id).select_related('profile')
                
                for user in mentioned_users:
                    create_notification(
                        sender=request.user,
                        recipient=user,
                        notification_type='mention',
                        message=f'You were mentioned in an event by @{request.user.username}',
                        related_object=event
                    )
                    if hasattr(user, 'profile') and user.profile.fcm_token:
                        send_push_notification_v1(
                            user.profile.fcm_token,
                            title="Event Mention",
                            body=f"You were mentioned in an event by @{request.user.username}"
                        )

            cache.delete_pattern('home_feed_*')
            cache.delete_pattern('event_list_*')
            return redirect('group_profile', pk=group.id) if group else redirect('users:profile', pk=request.user.id)
    else:
        form = EventForm()

    return render(request, 'activities/create_event.html', {
        'form': form,
        'group': group
    })

@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not post.can_edit(request.user):
        return redirect('users:profile', pk=request.user.id)
    
    group = post.group if post.group_id else None
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user, group=group)
        if form.is_valid():
            if 'image' in request.FILES:
                post.image = request.FILES['image']
            elif 'remove_image' in request.POST:
                post.image = None
            
            if 'video' in request.FILES:
                post.video = request.FILES['video']
            elif 'remove_video' in request.POST:
                post.video = None
                
            form.save()
            messages.success(request, 'Post updated!')
            cache.delete_pattern('home_feed_*')
            return redirect('group_profile', pk=post.group.id) if post.group else redirect('users:profile', pk=request.user.id)
    else:
        form = PostForm(instance=post, user=request.user, group=group)
        
    return render(request, 'activities/edit_post.html', {
        'form': form,
        'post': post
    })

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not post.can_delete(request.user):
        return redirect('users:profile', pk=request.user.id)
        
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted!')
        cache.delete_pattern('home_feed_*')
        return redirect('users:profile', pk=request.user.id)
        
    return render(request, 'activities/delete_confirm.html', {
        'cancel_url': post.get_absolute_url() if hasattr(post, 'get_absolute_url') else '/'
    })

# ======================
# INTERACTION VIEWS
# ======================

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id
    )
    
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    response_data = {
        'liked': created,
        'count': post.likes.count()
    }

    if not created:
        like.delete()
    elif post.author != request.user:
        create_notification(
            sender=request.user,
            recipient=post.author,
            notification_type='like',
            message=f'{request.user.username} liked your post',
            related_object=post
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response_data)
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
@require_POST
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    save, created = Save.objects.get_or_create(
        user=request.user,
        post=post
    )

    response_data = {
        'saved': created,
        'count': post.saves.count()
    }

    if not created:
        save.delete()
    elif post.author != request.user:
        create_notification(
            sender=request.user,
            recipient=post.author,
            notification_type='save',
            message=f'{request.user} saved your post.',
            related_object=post
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response_data)
        
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# ======================
# DETAIL VIEWS
# ======================

def event_detail(request, pk):
    event = get_object_or_404(
        Event.objects.select_related('creator', 'group')
                   .prefetch_related('attendees', 'registered_users'),
        pk=pk
    )
    
    # Permission checks
    if request.user.is_authenticated:
        event.user_can_edit = event.creator_id == request.user.id
        event.user_can_delete = event.creator_id == request.user.id
        event.user_is_attending = event.attendees.filter(id=request.user.id).exists()
        event.user_is_registered = event.registered_users.filter(id=request.user.id).exists()
    else:
        event.user_can_edit = False
        event.user_can_delete = False
        event.user_is_attending = False
        event.user_is_registered = False
    
    return render(request, 'activities/event_detail.html', {
        'event': event
    })

def post_detail(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group')
                   .prefetch_related(
                       'likes',
                       Prefetch('comments', queryset=Comment.objects.select_related('author'))
                   ),
        id=pk
    )
    
    return render(request, 'activities/post_detail.html', {
        'post': post,
        'comments': post.comments.all()[:100]
    })

# ======================
# GROUP MANAGEMENT VIEWS
# ======================

@login_required
def remove_user_from_group(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id)
    
    if hasattr(group, 'profile') and group.profile.creator == request.user:
        group.user_set.remove(user)
        
    return redirect('group_admin', group_id=group.id)

@login_required
def add_user_to_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_profile = getattr(group, 'profile', None)
    
    if not group_profile or group_profile.creator != request.user:
        return redirect('group_admin', group_id=group.id)
        
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(username__icontains=query)\
            .exclude(id__in=group.user_set.values_list('id', flat=True))
            
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            group.user_set.add(user)
            
            create_notification(
                sender=request.user,
                recipient=user,
                notification_type='group',
                message=f'You were added to the group {group.name}.',
                related_object=group
            )
            
            return redirect('group_admin', group_id=group.id)
            
    return render(request, 'activities/add_user_to_group.html', {
        'group': group,
        'query': query,
        'users': users,
    })

# ======================
# SEARCH & FILTER VIEWS
# ======================

@login_required
def search_and_filter_feed(request):
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter', 'recent')
    
    # Base queries
    posts = Post.objects.all()
    events = Event.objects.all()

    # Following filter
    if request.GET.get('following') == '1':
        following_ids = request.user.following.values_list('following_user', flat=True)
        posts = posts.filter(author__id__in=following_ids)
        events = events.filter(creator__id__in=following_ids)

    # Filter logic
    if filter_by == 'most_seen':
        posts = posts.order_by('-views') if hasattr(Post, 'views') else posts
        events = events.order_by('-views') if hasattr(Event, 'views') else events
    elif filter_by == 'most_comments':
        posts = posts.annotate(num_comments=Count('comment')).order_by('-num_comments')
        events = events.annotate(num_comments=Count('comment')).order_by('-num_comments')
    else:  # recent
        posts = posts.order_by('-created_at')
        events = events.order_by('-start_time')

    # Search logic
    if query:
        posts = posts.filter(
            Q(content__icontains=query) | 
            Q(author__username__icontains=query)
        )
        events = events.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(creator__username__icontains=query)
        )

    return render(request, 'activities/search_feed.html', {
        'posts': posts,
        'events': events,
        'query': query,
        'filter_by': filter_by,
    })

# ======================
# SHARING VIEWS
# ======================

@login_required
def share_page(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    following = User.objects.filter(followers__user=request.user)
    followers = User.objects.filter(following__following_user=request.user)
    post_url = request.build_absolute_uri(post.get_absolute_url())
    
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            recipient = get_user_model().objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect(request.path)
            
        # In a real implementation, use your messaging system
        from users.models_private_message import PrivateMessage
        PrivateMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            content=f"Shared a post: {post_url}"
        )
        
        messages.success(request, f'Post shared with {recipient.username}!')
        return redirect(post.get_absolute_url())
        
    return render(request, 'activities/share_page.html', {
        'post': post,
        'followers': followers,
        'following': following,
        'post_url': post_url,
    })

# ======================
# SPECIALTY VIEWS
# ======================

@login_required
def home_fellowship(request):
    from fellowship.models import FellowshipPost, FellowshipEvent, FellowshipMember
    
    fellowship_id = 1  # The main fellowship ID
    fellowship_posts = FellowshipPost.objects.filter(
        fellowship_id=fellowship_id
    ).order_by('-created_at')
    
    fellowship_events = FellowshipEvent.objects.filter(
        fellowship_id=fellowship_id
    ).order_by('-start_time')
    
    is_fellowship_member = False
    if request.user.is_authenticated:
        is_fellowship_member = FellowshipMember.objects.filter(
            fellowship_id=fellowship_id,
            user=request.user
        ).exists()
        
    return render(request, 'activities/home_fellowship.html', {
        'fellowship_posts': fellowship_posts,
        'fellowship_events': fellowship_events,
        'is_fellowship_member': is_fellowship_member,
    })