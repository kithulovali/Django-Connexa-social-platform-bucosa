from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
import random
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from .models import Post, Event, Comment, Like, Save, Share, Repost
from .forms import PostForm, EventForm, CommentForm
from django.contrib import messages
from .views_group_admin import group_admin
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from notifications.utils import create_notification
from django.utils import timezone

# Create your views here.
def home_activities(request):
    suggestions = []
    random_groups = []
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter', 'recent')
    posts = Post.objects.filter(group__isnull=True)
    # Only show events that have not ended
    events = Event.objects.filter(group__isnull=True, start_time__gte=timezone.now())
    # Filter by people you follow
    if request.user.is_authenticated and request.GET.get('following') == '1':
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
        posts = posts.filter(Q(content__icontains=query) | Q(author__username__icontains=query))
        # Show all fields of Post in the template, even if filtered
        posts = posts.select_related('author', 'group').prefetch_related('comments', 'group__profile')
        events = events.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(creator__username__icontains=query))
    followers = []
    following = []
    if request.user.is_authenticated:
        following = list(User.objects.filter(followers__user=request.user))
        followers = list(User.objects.filter(following__following_user=request.user))
    # Add absolute URL for each post for sharing
    for post in posts:
        if hasattr(post, 'get_absolute_url'):
            post.post_url = request.build_absolute_uri(post.get_absolute_url())
        else:
            post.post_url = ''
    # Only highlight in template, not in backend
    if request.user.is_authenticated:
        following_ids = request.user.following.values_list('following_user', flat=True)
        suggestions = list(User.objects.exclude(id__in=following_ids).exclude(id=request.user.id))
        random.shuffle(suggestions)
        suggestions = suggestions[:5]
    all_groups = list(Group.objects.all())
    random.shuffle(all_groups)
    random_groups = all_groups[:5]
    from django.conf import settings
    return render(request , 'activities/home_feed.html', {
        'suggestions': suggestions,
        'random_groups': random_groups,
        'posts': posts,
        'events': events,
        'query': query,
        'filter_by': filter_by,
        'followers': followers,
        'following': following,
        
    })

def post_activity(request):
    return render(request , 'activities/home_list.html')

def event_activity(request):
    events = Event.objects.all().order_by('-start_time')
    for event in events:
        event.can_edit = event.can_edit(request.user) if request.user.is_authenticated else False
        event.can_delete = event.can_delete(request.user) if request.user.is_authenticated else False
    return render(request, 'activities/event_list.html', {'events': events})

def group_activities(request): 
    return render(request ,'activities/group_detail.html')

@login_required
def create_post(request, group_id=None):
    group = None
    if group_id is not None:
        group = get_object_or_404(Group, id=group_id)
        if request.user not in group.user_set.all():
            return redirect('group_list')
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user, group=group)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # If group is disabled, set it explicitly
            if group:
                post.group = group
            post.save()
            # Push notification for new post
            if group:
                return redirect('group_profile', pk=group.id)
            else:
                return redirect('users:profile', pk=request.user.id)
    else:
        form = PostForm(user=request.user, group=group)
    return render(request, 'activities/create_post.html', {'form': form, 'group': group})

@login_required
def create_event(request, group_id=None):
    group = None
    # Accept group_id from GET if not provided as argument
    if group_id is None:
        group_id = request.GET.get('group_id')
    if group_id:
        group = get_object_or_404(Group, id=group_id)
        if request.user not in group.user_set.all():
            return redirect('group_list')
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            if group:
                event.group = group
            event.save()
            if group:
                return redirect('users:group_profile', pk=group.id)
            else:
                return redirect('users:profile', pk=request.user.id)
    else:
        form = EventForm()
    return render(request, 'activities/create_event.html', {'form': form, 'group': group})

@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not post.can_edit(request.user):
        return redirect('users:profile', pk=request.user.id)
    group = post.group if post.group_id else None
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user, group=group)
        if form.is_valid():
            # If a new image is uploaded, replace the old one
            if 'image' in request.FILES:
                post.image = request.FILES['image']
            elif 'remove_image' in request.POST:
                post.image = None
            # If a new video is uploaded, replace the old one
            if 'video' in request.FILES:
                post.video = request.FILES['video']
            elif 'remove_video' in request.POST:
                post.video = None
            form.save()
            messages.success(request, 'Post updated!')
            if post.group:
                return redirect('group_profile', pk=post.group.id)
            else:
                return redirect('users:profile', pk=request.user.id)
    else:
        form = PostForm(instance=post, user=request.user, group=group)
    return render(request, 'activities/edit_post.html', {'form': form, 'post': post})

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not post.can_delete(request.user):
        return redirect('users:profile', pk=request.user.id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted!')
        return redirect('users:profile', pk=request.user.id)
    return render(request, 'activities/delete_confirm.html', {'cancel_url': post.get_absolute_url() if hasattr(post, 'get_absolute_url') else '/'})

@login_required
def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not event.can_edit(request.user):
        return redirect('users:profile', pk=request.user.id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated!')
            return redirect('users:profile', pk=request.user.id)
    else:
        form = EventForm(instance=event)
    return render(request, 'activities/edit_event.html', {'form': form, 'event': event})

@login_required
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not event.can_delete(request.user):
        return redirect('users:profile', pk=request.user.id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted!')
        return redirect('users:profile', pk=request.user.id)
    return render(request, 'activities/delete_confirm.html', {'cancel_url': event.get_absolute_url() if hasattr(event, 'get_absolute_url') else '/'})

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    event.can_edit = event.can_edit(request.user) if request.user.is_authenticated else False
    event.can_delete = event.can_delete(request.user) if request.user.is_authenticated else False
    return render(request, 'activities/event_detail.html', {'event': event})

@login_required
def remove_user_from_group(request, group_id, user_id):
    group = get_object_or_404(Group, id=group_id)
    user = get_object_or_404(User, id=user_id)
    # Only the group creator can remove users
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
        users = User.objects.filter(username__icontains=query).exclude(id__in=group.user_set.values_list('id', flat=True))
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            group.user_set.add(user)
            # Notify user added to group
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

@require_POST
@login_required
def attend_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user not in event.attendees.all():
        event.attendees.add(request.user)
        # Notify event creator
        if event.creator != request.user:
            create_notification(
                sender=request.user,
                recipient=event.creator,
                notification_type='event',
                message=f'{request.user} is attending your event: {event.title}',
                related_object=event
            )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user not in event.registered_users.all():
        event.registered_users.add(request.user)
        # Notify event creator
        if event.creator != request.user:
            create_notification(
                sender=request.user,
                recipient=event.creator,
                notification_type='event_registration',
                message=f'{request.user.get_full_name() or request.user.username} registered for your event: {event.title}',
                related_object=event
            )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def search_and_filter_feed(request):
    user = request.user
    query = request.GET.get('q', '')
    filter_by = request.GET.get('filter', 'recent')
    posts = Post.objects.all()
    events = Event.objects.all()
    # Filter by people you follow
    if request.GET.get('following') == '1':
        following_ids = user.following.values_list('following_user', flat=True)
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
        posts = posts.filter(Q(content__icontains=query) | Q(author__username__icontains=query))
        events = events.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(creator__username__icontains=query))
    return render(request, 'activities/search_feed.html', {
        'posts': posts,
        'events': events,
        'query': query,
        'filter_by': filter_by,
    })

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            # Notify post author (if not self)
            if post.author != request.user:
                create_notification(
                    sender=request.user,
                    recipient=post.author,
                    notification_type='comment',
                    message=f'{request.user} commented: {comment.content[:50]}',
                    related_object=comment
                )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        # Notify post author (if not self)
        if post.author != request.user:
            from notifications.utils import create_notification
            create_notification(
                sender=request.user,
                recipient=post.author,
                notification_type='like',
                message=f'{request.user} liked your post.',
                related_object=post
            )
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.likes.count()})
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    save, created = Save.objects.get_or_create(user=request.user, post=post)
    if not created:
        save.delete()
        saved = False
    else:
        saved = True
        # Notify post author (if not self)
        if post.author != request.user:
            create_notification(
                sender=request.user,
                recipient=post.author,
                notification_type='save',
                message=f'{request.user} saved your post.',
                related_object=post
            )
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved, 'count': post.saves.count()})
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def share_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Share.objects.create(user=request.user, post=post)
    # Notify post author (if not self)
    if post.author != request.user:
        create_notification(
            sender=request.user,
            recipient=post.author,
            notification_type='share',
            message=f'{request.user} shared your post.',
            related_object=post
        )
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'shared': True, 'count': post.shares.count()})
    messages.success(request, 'Post shared!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def repost_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Prevent reposting your own post
    if post.author == request.user:
        messages.error(request, "You can't repost your own post.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    # Always reference the original post for reposts
    original = post.repost_of if post.repost_of else post
    # Prevent reposting the same post multiple times
    if Post.objects.filter(author=request.user, repost_of=original).exists():
        messages.info(request, "You've already reposted this post.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    repost = Post.objects.create(author=request.user, repost_of=original)
    # Notify original post author (if not self)
    if original.author != request.user:
        create_notification(
            sender=request.user,
            recipient=original.author,
            notification_type='repost',
            message=f'{request.user} reposted your post.',
            related_object=repost
        )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def user_reposts(request, user_id=None):
    from django.contrib.auth.models import User
    if user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user
    reposts = Repost.objects.filter(user=user).select_related('post').order_by('-created_at')
    posts = [r.post for r in reposts]
    return render(request, 'activities/user_reposts.html', {'posts': posts, 'profile_user': user})

@login_required
def saved_posts(request):
    saved = request.user.save_set.select_related('post').all()
    posts = [s.post for s in saved]
    return render(request, 'activities/saved_posts.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, id=pk)
    return render(request, 'activities/post_detail.html', {'post': post})

@login_required
def share_to_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        post_id = request.POST.get('post_id')
        User = get_user_model()
        try:
            recipient = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        post = get_object_or_404(Post, id=post_id)
        # For demo: send as a private message (or notification)
        # You can customize this to use your actual messaging system
        from users.models_private_message import PrivateMessage
        PrivateMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            content=f"Shared a post: {request.build_absolute_uri(post.get_absolute_url())}"
        )
        messages.success(request, f'Post shared with {recipient.username}!')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

@login_required
def share_page(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    following = User.objects.filter(followers__user=request.user)
    followers = User.objects.filter(following__following_user=request.user)
    post_url = request.build_absolute_uri(post.get_absolute_url())
    if request.method == 'POST':
        username = request.POST.get('username')
        UserModel = get_user_model()
        try:
            recipient = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect(request.path)
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

@login_required
def home_fellowship(request):
    from fellowship.models import FellowshipPost, FellowshipEvent, FellowshipMember, fellowship_edit
    fellowship_id = 1  # The main fellowship ID
    fellowship_posts = FellowshipPost.objects.filter(fellowship_id=fellowship_id).order_by('-created_at')
    fellowship_events = FellowshipEvent.objects.filter(fellowship_id=fellowship_id).order_by('-start_time')
    is_fellowship_member = False
    if request.user.is_authenticated:
        is_fellowship_member = FellowshipMember.objects.filter(fellowship_id=fellowship_id, user=request.user).exists()
    return render(request, 'activities/home_fellowship.html', {
        'fellowship_posts': fellowship_posts,
        'fellowship_events': fellowship_events,
        'is_fellowship_member': is_fellowship_member,
    })