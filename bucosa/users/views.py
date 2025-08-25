from django.db.models import Q
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import get_user_model, login, logout, authenticate, update_session_auth_hash
import datetime
from django.conf import settings
import json
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)



@login_required
@require_http_methods(["POST"])
def welcome_next(request):
    return redirect('home')  
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Count, Max, Prefetch, Exists, OuterRef
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

# Third-party imports
from allauth.socialaccount.models import SocialAccount
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Local imports
from .forms import profileForm, ProfileUpdateForm, GroupCreateForm, GroupProfileForm
from .models import user_profile, GroupProfile, user_following, Invitation
from django.db.models import Q
from .models import GroupJoinRequest
from .models_block_report import UserBlock, UserReport
from .models_group_message import GroupMessage
from .models_staff_message import staff_messages
from notifications.utils import create_notification, send_custom_notification_email
from django.core.mail import send_mail
from .utils import get_display_name
from .models_private_message import PrivateMessage
from activities.models import Post, Event, Repost, Save

from users.models import user_profile, user_following

# API endpoint for unread private message count
@login_required
@require_GET
def api_unread_messages_count(request):
    count = PrivateMessage.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_messages_count': count})


# Create your views here.
from django.urls import reverse

# Request to join a group
from django.views.decorators.http import require_POST

@login_required
@require_POST
def request_join_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.user in group.user_set.all():
        messages.info(request, "You are already a member of this group.")
        return redirect('users:group_profile', pk=group_id)
    existing_request = GroupJoinRequest.objects.filter(user=request.user, group=group).first()
    if existing_request:
        if existing_request.approved:
            messages.info(request, "Your request has already been approved.")
        elif existing_request.rejected:
            messages.warning(request, "Your previous request was rejected.")
        else:
            messages.info(request, "You have already requested to join. Please wait for admin approval.")
        return redirect('users:group_profile', pk=group_id)
    GroupJoinRequest.objects.create(user=request.user, group=group)
    messages.success(request, "Your request to join the group has been sent.")
    return redirect('users:group_profile', pk=group_id)

# Admin view to manage join requests
@login_required
def manage_group_requests(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    group_profile = getattr(group, 'profile', None)
    if not group_profile or request.user not in group_profile.admins.all():
        return HttpResponseForbidden("Only group admins can manage join requests.")
    requests = GroupJoinRequest.objects.filter(group=group, approved=False, rejected=False)
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(GroupJoinRequest, pk=req_id, group=group)
        if action == 'approve':
            join_request.approved = True
            join_request.reviewed_at = timezone.now()
            join_request.save()
            group.user_set.add(join_request.user)
            # Send email notification to user
            if join_request.user.email:
                from django.core.mail import send_mail
                subject = f"Your request to join '{group.name}' was approved!"
                group_url = group.profile.get_absolute_url() if hasattr(group, 'profile') else f"/groups/{group.id}/"
                message = (
                    f"Hi {join_request.user.username},\n\n"
                    f"Your request to join the group '{group.name}' has been approved.\n"
                    f"You can now access the group and participate in the chat!\n\n"
                    f"Go to the group: https://{request.get_host()}{group_url}\n\n"
                    f"Blessings,\nThe Bucosa Team"
                )
                send_mail(subject, message, None, [join_request.user.email], fail_silently=True)
            messages.success(request, f"Approved {join_request.user.username}.")
        elif action == 'reject':
            join_request.rejected = True
            join_request.reviewed_at = timezone.now()
            join_request.save()
            messages.info(request, f"Rejected {join_request.user.username}.")
        return redirect('users:manage_group_requests', group_id=group_id)
    return render(request, 'users/manage_group_requests.html', {'group': group, 'requests': requests})

from django.urls import reverse

@login_required
def invite(request):
    invite_link = None
    if request.method == 'POST':
        if request.POST.get('generate_link'):
            # Generate link without email or phone
            invitation = Invitation.objects.create(inviter=request.user)
            invite_link = request.build_absolute_uri(invitation.get_invite_link())
        else:
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            invitation = Invitation.objects.create(
                inviter=request.user,
                email=email if email else None,
                phone=phone if phone else None
            )
            invite_link = request.build_absolute_uri(invitation.get_invite_link())
            if email:
                send_invitation_email(email, invite_link)
            if phone:
                send_invitation_sms(phone, invite_link)
    return render(request, 'users/invite.html', {'invite_link': invite_link})

# users/utils.py
def safe_get_or_create_profile(user, defaults=None):
    """
    Safely gets or creates a user profile with error handling
    Usage: profile = safe_get_or_create_profile(request.user)
    """
    if defaults is None:
        defaults = {}
    
    try:
        # Try to get existing profile
        return user_profile.objects.get(user=user)
    except ObjectDoesNotExist:
        try:
            # Try to create new profile
            return user_profile.objects.create(user=user, **defaults)
        except IntegrityError:
            # If creation fails (race condition), get the profile
            return user_profile.objects.get(user=user)


def get_or_create_user_profile(user):
    """One-function solution combining the best of #1 and #2"""
    # Phase 1: Get best available email
    email = user.email or ''
    
    # Optimized social account check (single query)
    try:
        social = SocialAccount.objects.filter(user=user, provider='google').first()
        if social:
            email = social.extra_data.get('email', email)
            # Update username if default-ish
            if (social.extra_data.get('given_name') and 
                (not user.username or user.username == user.email)):
                user.username = social.extra_data['given_name']
                user.save(update_fields=['username'])
    except Exception:
        pass  # Skip if social account check fails

    # Phase 2: Profile creation with atomic retries
    try:
        with transaction.atomic():
            profile, _ = user_profile.objects.get_or_create(
                user=user,
                defaults={'email': email}
            )
            return profile
    except IntegrityError:
        # Handle race condition or email conflict
        try:
            return user_profile.objects.get(user=user)
        except ObjectDoesNotExist:
            # Fallback: Create without email
            return user_profile.objects.create(user=user, email='')
# Show followers list
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def admin_delete_user(request, username):
    try:
        target_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, f'No user found with username "{username}".')
        return redirect('users:settings')
    if request.method == 'POST':
        target_user.delete()
        messages.success(request, f'User {target_user.username} has been deleted.')
        return redirect('users:settings')
    return render(request, 'users/admin_delete_user_confirm.html', {'target_user': target_user})

@login_required
def followers_list(request, pk):
    user = get_object_or_404(get_user_model(), id=pk)
    followers = user.followers.all()
    return render(request, 'users/followers_list.html', {'profile_user': user, 'followers': followers})

# Show following list
@login_required
def following_list(request, pk):
    user = get_object_or_404(get_user_model(), id=pk)
    following_users = get_user_model().objects.filter(
        id__in=user.following.values_list('following_user_id', flat=True)
    ).distinct()
    return render(request, 'users/following_list.html', {'profile_user': user, 'following': following_users})
# Admin-only delete user view      
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
                messages.error(request ,'Incorrect password')
    return render(request , 'users/login.html', {

    })

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
            # Update user info from social account if available
            try:
                social = SocialAccount.objects.filter(user=user).first()
                if social:
                    extra = social.extra_data
                    # Update first_name, last_name, email if present
                    if extra.get('given_name'):
                        user.first_name = extra['given_name']
                    if extra.get('family_name'):
                        user.last_name = extra['family_name']
                    if extra.get('email'):
                        user.email = extra['email']
                    user.save()
            except Exception:
                pass
            import logging
            logger = logging.getLogger(__name__)
            # Send welcome email if user has email
            if user.email:
                display_name = get_display_name(user)
                try:
                    subject = 'Welcome to Bucosa!'
                    message = (
                        f"Hi {display_name},\n\n"
                        "Welcome to Bucosa, your new social platform for faith, fellowship, and community!\n\n"
                        "We're excited to have you join us. Here you can connect with others, share your journey, and grow together.\n\n"
                        "If you have any questions or need help, reply to this email or visit our help center.\n\n"
                        "Blessings,\nThe Bucosa Team"
                    )
                    from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else ""
                    send_mail(
                        subject,
                        message,
                        from_email,
                        [user.email],
                        fail_silently=False,
                    )
                    logger.info(f"Welcome email sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send welcome email to {user.email}: {e}")
            # Always create default welcome post for every user
            from activities.models import Post
            try:
                if user.first_name or user.last_name:
                    welcome_name = f"{user.first_name} {user.last_name}".strip()
                elif user.email:
                    welcome_name = user.email
                else:
                    welcome_name = user.username
                post = Post.objects.create(
                    author=user,
                    content=f"🌟🌟✨✨ Welcome {welcome_name} to Bucosa! We're excited to have you join our community. Feel free to explore, connect, and share your first post!",
                    privacy="PRIVATE",
                    is_welcome_post=True
                )
                logger.info(f"Welcome post created for new user {user.username} (post id: {post.id})")
            except Exception as e:
                logger.error(f"Failed to create welcome post for new user {user.username}: {e}")
            return redirect('users:welcome')
        else :
            messages.error(request ,'Registration failed please try again!')
    return render(request , 'users/register.html' , {'form': form})

#=============profile view - HEAVILY OPTIMIZED

@require_http_methods(["GET", "POST"])
def welcome(request):
    if request.user.is_authenticated:
        return redirect('activities:home')
    else:
        return render(request, 'users/welcome.html', {'user': request.user})

def profile_user(request, pk):
    # Early validation
    if not pk or pk == 'None':
        messages.error(request, 'Invalid user profile requested.')
        return redirect('/')

    # Base cache keys
    cache_key = f'user_profile_full_{pk}'
    auth_user_id = request.user.id if request.user.is_authenticated else None
    
    # Try to get cached response
    cached_response = cache.get(cache_key)
    if cached_response and cached_response.get('auth_user_id') == auth_user_id:
        return render(request, 'users/profile.html', cached_response['context'])

    try:
        # Get user with select_related for common joins
        user = User.objects.select_related('profile').get(id=pk)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('/')

    # Check if we have a profile or need to create one
    profile = getattr(user, 'profile', None)
    if not profile:
        profile = create_or_update_user_profile(user)

    # Prefetch all related data in optimized queries
    posts_prefetch = Prefetch(
        'post_set',
        queryset=Post.objects.select_related('author').order_by('-created_at')[:20],
        to_attr='prefetched_posts'
    )
    
    events_prefetch = Prefetch(
        'event_set',
        queryset=Event.objects.select_related('creator').order_by('-start_time')[:10],
        to_attr='prefetched_events'
    )
    
    reposts_prefetch = Prefetch(
        'repost_set',
        queryset=Repost.objects.select_related('user', 'post__author').order_by('-created_at')[:10],
        to_attr='prefetched_reposts'
    )
    
    saved_posts_prefetch = Prefetch(
        'save_set',
        queryset=Save.objects.select_related('post__author').order_by('-created_at')[:10],
        to_attr='prefetched_saves'
    )

    # Get the user with all prefetched data in a single query
    user = User.objects.filter(id=pk).prefetch_related(
        posts_prefetch,
        events_prefetch,
        reposts_prefetch,
        saved_posts_prefetch,
        Prefetch('groups', queryset=Group.objects.all()[:10], to_attr='prefetched_groups')
    ).annotate(
        followers_count=Count('followers', distinct=True),
        following_count=Count('following', distinct=True),
        is_following=Exists(
            user_following.objects.filter(
                user_id=auth_user_id,
                following_user_id=pk
            )
        ) if auth_user_id else False
    ).first()

    # Prepare context with all data
    saved_posts = []
    if hasattr(user, 'prefetched_saves'):
        saved_posts = [save.post for save in user.prefetched_saves]
    
    context = {
        'user': user,
        'profile': profile,
        'is_following': getattr(user, 'is_following', False),
        'followers_count': getattr(user, 'followers_count', 0),
        'following_count': getattr(user, 'following_count', 0),
        'user_groups': getattr(user, 'prefetched_groups', []),
        'posts': getattr(user, 'prefetched_posts', []),
        'reposts': getattr(user, 'prefetched_reposts', []),
        'saved_posts': saved_posts,
        'events': getattr(user, 'prefetched_events', []),
    }

    # Cache the full response for 5 minutes
    cache.set(cache_key, {
        'context': context,
        'auth_user_id': auth_user_id
    }, 300)

    return render(request, 'users/profile.html', context)

def create_or_update_user_profile(user):
    """Handle profile creation/update in a separate function"""
    email = user.email
    google_first_name = None
    
    try:
        social = SocialAccount.objects.filter(user=user, provider='google').first()
        if social:
            google_first_name = social.extra_data.get('given_name')
            email = social.extra_data.get('email', email)
            
            if google_first_name and (user.username == user.email or user.username == '' or user.username.startswith('user')):
                user.username = google_first_name
                user.save(update_fields=['username'])
    except Exception:
        pass

    # Use our safe utility function
    profile = safe_get_or_create_profile(user, defaults={'email': email})
    
    # Update email if it's different
    if profile.email != email:
        profile.email = email
        profile.save(update_fields=['email'])
        
    return profile

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
            # Ensure the followed user appears in the follower's private messages list
            from .models_private_message import PrivateMessage
            from django.db.models import Q
            exists = PrivateMessage.objects.filter(
                (Q(sender=request.user) & Q(recipient=target_user)) |
                (Q(sender=target_user) & Q(recipient=request.user))
            ).exists()
            if not exists:
                PrivateMessage.objects.create(
                    sender=request.user,
                    recipient=target_user,
                    content="",
                    is_read=True
                )

            
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

    # Access control logic
    is_member = request.user in members
    is_admin = group_profile and request.user in group_profile.admins.all()
    # Check invitation
    # Safely check for user.profile and phone
    user_phone = None
    try:
        user_phone = request.user.profile.phone
    except Exception:
        user_phone = None
    invited = Invitation.objects.filter(
        (Q(email=request.user.email) | Q(phone=user_phone)),
        accepted=False
    ).exists()
    # Check approved join request
    from .models import GroupJoinRequest
    approved_request = GroupJoinRequest.objects.filter(user=request.user, group=group, approved=True).exists()
    can_access = is_member or invited or approved_request or is_admin

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

    # If not allowed, show join/invite/request options
    show_request_to_join = not can_access and not GroupJoinRequest.objects.filter(user=request.user, group=group, approved=False, rejected=False).exists()
    show_pending = not can_access and GroupJoinRequest.objects.filter(user=request.user, group=group, approved=False, rejected=False).exists()

    if not can_access:
        return render(request, 'users/group_access_limited.html', {
            'group': group,
            'group_profile': group_profile,
            'show_request_to_join': show_request_to_join,
            'show_pending': show_pending,
        })

    return render(request, 'users/group_profile.html', {
        'group': group,
        'group_profile': group_profile,
        'members': members,
        'group_posts': group_posts,
        'group_events': group_events,
        'is_admin': is_admin,
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
    
    # Check membership
    if not group.user_set.filter(id=request.user.id).exists():
        return HttpResponseForbidden('You must be a member to view the chat.')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        file = request.FILES.get('file')
        
        if content or file:
            msg = GroupMessage.objects.create(
                group=group, user=request.user, content=content, file=file
            )
            
            # WebSocket broadcast
            if channel_layer := get_channel_layer():
                async_to_sync(channel_layer.group_send)(
                    f"group_{group.id}",
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
    return render(request, 'users/group_chat.html', {
        'group': group, 
        'messages': GroupMessage.objects.filter(group=group)
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

    # Get groups where user is a member
    from django.contrib.auth.models import Group
    user_groups = Group.objects.filter(user=request.user)
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query)


    other_user = None
    error_message = None
    if user_id:
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            error_message = "The user you are trying to message does not exist."

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
    if other_user and not error_message:
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
            # Send notification and email
            notification = create_notification(
                sender=request.user,
                recipient=other_user,
                notification_type='message',
                message=f'New private message from {request.user.username}',
                related_object=msg
            )
            if other_user.email:
                send_custom_notification_email(notification, other_user)
            
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
    context = {
        'other_user': other_user,
        'messages': messages_qs,
        'users': users,
        'search_query': search_query,
        'unread_counts': unread_counts,
        'user_groups': user_groups,
        'error_message': error_message,
    }

    return render(request, 'users/private_messages.html', context)

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

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('users:login')
    return render(request, 'users/delete_account_confirm.html')

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
        # Handle case where profile doesn't exist - use our safe utility
        profile = safe_get_or_create_profile(request.user)
        
    if request.method == 'POST':
        privacy = request.POST.get('privacy')
        if privacy in dict(profile.PRIVACY_CHOICES):
            profile.privacy = privacy
            profile.save(update_fields=['privacy'])
            messages.success(request, 'Privacy settings updated.')
            return redirect('users:profile', pk=request.user.id)
            
    return render(request, 'users/edit_privacy.html', {'profile': profile})

@login_required
def friend_suggestions(request):
    # Suggest users not already followed, not self, not blocked
    following_ids = request.user.following.values_list('following_user_id', flat=True)
    blocked_ids = UserBlock.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
    
    suggestions = User.objects.filter(is_active=True).exclude(
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

def send_invitation_email(email, invite_link):
    subject = "You're invited!"
    message = f"You have been invited. Click the link to join: {invite_link}"
    send_mail(subject, message, None, [email])

def send_invitation_sms(phone, invite_link):
    # Integrate with SMS provider here
    pass

@login_required
def accept_invite(request, token):
    invitation = Invitation.objects.filter(link_token=token).first()
    if not invitation:
        return render(request, 'users/accept_invite.html', {'invitation': None})
    if request.method == 'POST' and not invitation.accepted:
        invitation.accepted = True
        invitation.accepted_at = timezone.now()
        invitation.save()
        # Optionally, add user to group or perform other actions
    return render(request, 'users/accept_invite.html', {'invitation': invitation})

@login_required
def your_groups_list(request):
    # Groups where user is creator or admin (no duplicates, sorted)
    group_ids = GroupProfile.objects.filter(Q(admins=request.user) | Q(creator=request.user)).values_list('group_id', flat=True).distinct()
    groups = Group.objects.filter(id__in=group_ids).select_related('profile').order_by('name')
    return render(request, 'users/your_groups_list.html', {'groups': groups})


def staff_required(user):
    return user.is_authenticated and user.is_staff

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .models import staff_messages

@user_passes_test(lambda u: u.is_staff)
def staff_messages(request):
    # Get all messages (group chat - everyone sees everything)
    all_messages = staff_messages.objects.all().order_by('created_at')
    
    # Get all staff users for online count
    staff_users = User.objects.filter(is_staff=True)
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        
        if message_text:
            # Create message - automatically goes to all staff
            new_message = staff_messages.objects.create(
                sender=request.user,
                message=message_text,
                subject="Group Chat"  # Default subject for group messages
            )
            
            # Add all staff members as recipients
            new_message.recipients.set(staff_users)
            
            # Handle file upload
            if 'image' in request.FILES:
                new_message.image = request.FILES['image']
                new_message.save()
            
            return redirect('users:staff_messages')
    
    context = {
        'messages': all_messages,
        'staff_users': staff_users,
    }
    return render(request, 'users/staff_messages.html', context)