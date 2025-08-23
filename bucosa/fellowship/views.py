from django.contrib.contenttypes.models import ContentType
from activities.models import GenericLike, GenericComment, GenericShare
from django.contrib.auth.decorators import login_required
from .models import MembershipRequest, FellowshipMember, fellowship_edit, donation, FellowshipPost, FellowshipEvent, Profile
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from . forms import donationForm, fellowship_editForm, ProfileForm
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import Notification
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Count, Prefetch
from django.http import JsonResponse
import logging
from threading import Thread

logger = logging.getLogger(__name__)

# Create your views here.
@login_required
def fellowship_view(request):
    edit = fellowship_edit.objects.all().only('id', 'name', 'image')
    context = {
        'edit': edit
    }
    return render(request, 'fellowship/fellowship.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_fellowship(request, fellowship_id):
    fellowship_instance = get_object_or_404(fellowship_edit, id=fellowship_id)
    if request.method == 'POST':
        form = fellowship_editForm(request.POST, request.FILES, instance=fellowship_instance)
        if form.is_valid():
            form.save()
            cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
            return redirect('fellowship_detail', fellowship_id=fellowship_id)
    else:
        form = fellowship_editForm(instance=fellowship_instance)
    return render(request, 'fellowship/edit_fellowship.html', {'form': form, 'fellowship': fellowship_instance})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_fellowship_model(request, fellowship_id):
    fellowship_instance = get_object_or_404(fellowship_edit, id=fellowship_id)
    if request.method == 'POST':
        form = fellowship_editForm(request.POST, request.FILES, instance=fellowship_instance)
        if form.is_valid():
            form.save()
            cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
            return redirect('fellowship_detail', fellowship_id=fellowship_id)
    else:
        form = fellowship_editForm(instance=fellowship_instance)
    context = {
        'form': form,
        'fellowship': fellowship_instance
    }
    return render(request, 'fellowship/edit_fellowship_model.html', context)

def donate_view(request):
    form = donationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            donate = form.save(commit=False)
            donate.save()
            return redirect('/fellowship/donate/?success=1')
    return render(request, 'fellowship/donate.html', {'form': form})

@login_required
def join_fellowship(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    
    if FellowshipMember.objects.filter(fellowship=fellowship, user=request.user).exists():
        messages.info(request, "You are already a member.")
        return redirect('fellowship_detail', fellowship_id=fellowship.id)
    
    if MembershipRequest.objects.filter(fellowship=fellowship, user=request.user, accepted=False).exists():
        messages.info(request, "You have already requested to join.")
        return redirect('fellowship_detail', fellowship_id=fellowship.id)
    
    MembershipRequest.objects.create(fellowship=fellowship, user=request.user)
    messages.success(request, "Your request to join has been sent to the admin.")
    return redirect('fellowship_detail', fellowship_id=fellowship.id)

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@superuser_required
def create_fellowship_post(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        
        if content:
            post = FellowshipPost.objects.create(
                fellowship=fellowship,
                author=request.user,
                content=content,
                image=image,
                video=video
            )
            
            cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
            
            def send_notifications_async():
                try:
                    members = FellowshipMember.objects.filter(
                        fellowship=fellowship
                    ).exclude(user=request.user).select_related('user')
                    
                    for member in members:
                        Notification.objects.create(
                            sender=request.user,
                            recipient=member.user,
                            notification_type='other',
                            message=f'New post in {fellowship.name}.'
                        )
                    
                    active_users = User.objects.filter(
                        is_active=True
                    ).exclude(
                        id=request.user.id
                    ).exclude(
                        email=''
                    ).exclude(
                        email__isnull=True
                    ).values_list('email', flat=True)[:100]  # Limit to 100 emails
                    
                    if active_users:
                        fellowship_url = request.build_absolute_uri(f'/fellowship/{fellowship.id}/')
                        subject = 'Bucosa Fellowship Posted'
                        message = f'{request.user.username} posted in {fellowship.name}:\n\n{content[:100]}...\n\nView on site: {fellowship_url}'
                        from_email = settings.DEFAULT_FROM_EMAIL
                        
                        for email in active_users:
                            try:
                                send_mail(subject, message, from_email, [email], fail_silently=True)
                            except Exception as e:
                                logger.error(f"Error sending email to {email}: {e}")
                                
                except Exception as e:
                    logger.error(f"Error sending notifications: {e}")
            
            Thread(target=send_notifications_async).start()
            
            return redirect('fellowship_detail', fellowship_id=fellowship.id)
    
    return render(request, 'fellowship/create_post.html', {'fellowship': fellowship})

@superuser_required
def create_fellowship_event(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        location = request.POST.get('location', '').strip()
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        cover_image = request.FILES.get('cover_image')
        
        if title and start_time and end_time:
            event = FellowshipEvent.objects.create(
                fellowship=fellowship,
                creator=request.user,
                title=title,
                description=description,
                location=location,
                start_time=start_time,
                end_time=end_time,
                cover_image=cover_image
            )
            
            cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
            
            def send_event_notifications_async():
                try:
                    members = FellowshipMember.objects.filter(
                        fellowship=fellowship
                    ).exclude(user=request.user).select_related('user')
                    
                    for member in members:
                        Notification.objects.create(
                            sender=request.user,
                            recipient=member.user,
                            notification_type='other',
                            message=f'New event "{event.title}" in {fellowship.name}.'
                        )
                    
                    active_users = User.objects.filter(
                        is_active=True
                    ).exclude(
                        id=request.user.id
                    ).exclude(
                        email=''
                    ).exclude(
                        email__isnull=True
                    ).values_list('email', flat=True)[:100]
                    
                    if active_users:
                        fellowship_url = request.build_absolute_uri(f'/fellowship/{fellowship.id}/')
                        subject = 'Join the Fellowship Event'
                        message = f'{request.user.username} created an event in {fellowship.name}: {title}\n\nDescription: {description[:200]}...\nLocation: {location}\nStart: {start_time}\nEnd: {end_time}\n\nJoin or view event: {fellowship_url}'
                        from_email = settings.DEFAULT_FROM_EMAIL
                        
                        for email in active_users:
                            try:
                                send_mail(subject, message, from_email, [email], fail_silently=True)
                            except Exception as e:
                                logger.error(f"Error sending email to {email}: {e}")
                                
                except Exception as e:
                    logger.error(f"Error sending event notifications: {e}")
            
            Thread(target=send_event_notifications_async).start()
            
    return render(request, 'fellowship/create_event.html', {'fellowship': fellowship})

@login_required
def fellowship_detail(request, fellowship_id):
    cache_key = f'fellowship_detail_{fellowship_id}_{request.user.id}'
    cached_response = cache.get(cache_key)
    
    if cached_response:
        return render(request, 'fellowship/fellowship_detail.html', cached_response)
    
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    
    post_ct = ContentType.objects.get_for_model(FellowshipPost)
    
    posts = FellowshipPost.objects.filter(
        fellowship=fellowship, 
        author=fellowship.admin
    ).select_related('author').prefetch_related(
        Prefetch(
            'genericcomment_set',
            queryset=GenericComment.objects.select_related('author').order_by('created_at')[:10],
            to_attr='prefetched_comments'
        )
    ).order_by('-created_at')
    
    posts = posts.annotate(
        like_count=Count('genericlike', distinct=True),
        comment_count=Count('genericcomment', distinct=True)
    )
    
    events = FellowshipEvent.objects.filter(fellowship=fellowship).select_related('creator').order_by('-start_time')[:10]
    members = FellowshipMember.objects.filter(fellowship=fellowship).select_related('user')[:20]
    
    is_member = FellowshipMember.objects.filter(fellowship=fellowship, user=request.user).exists()
    is_admin = fellowship.admin == request.user
    followers_count = FellowshipMember.objects.filter(fellowship=fellowship).count()

    profile_fellowship = None
    if hasattr(fellowship, 'fellowship_profile'):
        profile_fellowship = fellowship.fellowship_profile

    context = {
        'fellowship': fellowship,
        'fellowship_posts': posts,
        'events': events,
        'members': members,
        'is_member': is_member,
        'is_admin': is_admin,
        'followers_count': followers_count,
        'profile_fellowship': profile_fellowship,
    }
    
    cache.set(cache_key, context, 300)
    
    return render(request, 'fellowship/fellowship_detail.html', context)

@login_required
def fellowship_admin_dashboard(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    
    if fellowship.admin != request.user and not request.user.is_superuser:
        return redirect('fellowship_detail', fellowship_id=fellowship.id)
    
    members = FellowshipMember.objects.filter(fellowship=fellowship).select_related('user')
    posts = FellowshipPost.objects.filter(fellowship=fellowship).select_related('author')[:50]
    events = FellowshipEvent.objects.filter(fellowship=fellowship).select_related('creator')[:20]
    membership_requests = MembershipRequest.objects.filter(
        fellowship=fellowship, 
        accepted=False
    ).select_related('user')
    
    return render(request, 'fellowship/fellowship_admin.html', {
        'fellowship': fellowship,
        'members': members,
        'posts': posts,
        'events': events,
        'membership_requests': membership_requests,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_my_posts_events(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    posts = FellowshipPost.objects.filter(fellowship=fellowship, author=request.user).select_related('fellowship')
    events = FellowshipEvent.objects.filter(fellowship=fellowship, creator=request.user).select_related('fellowship')
    return render(request, 'fellowship/admin_my_posts_events.html', {
        'fellowship': fellowship,
        'posts': posts,
        'events': events,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_fellowship_post(request, fellowship_id, post_id):
    post = get_object_or_404(FellowshipPost, id=post_id, fellowship_id=fellowship_id, author=request.user)
    if request.method == 'POST':
        form = fellowship_editForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
            return redirect('admin_my_posts_events', fellowship_id=fellowship_id)
    else:
        form = fellowship_editForm(instance=post)
    return render(request, 'fellowship/edit_fellowship_post.html', {'form': form, 'fellowship': post.fellowship, 'post': post})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_fellowship_post(request, fellowship_id, post_id):
    post = get_object_or_404(FellowshipPost, id=post_id, fellowship_id=fellowship_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
        return redirect('admin_my_posts_events', fellowship_id=fellowship_id)
    return render(request, 'fellowship/confirm_delete.html', {'object': post, 'type': 'post'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_fellowship_event(request, fellowship_id, event_id):
    event = get_object_or_404(FellowshipEvent, id=event_id, fellowship_id=fellowship_id, creator=request.user)
    if request.method == 'POST':
        form = fellowship_editForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
            return redirect('admin_my_posts_events', fellowship_id=fellowship_id)
    else:
        form = fellowship_editForm(instance=event)
    return render(request, 'fellowship/edit_fellowship_event.html', {'form': form, 'fellowship': event.fellowship, 'event': event})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_fellowship_event(request, fellowship_id, event_id):
    event = get_object_or_404(FellowshipEvent, id=event_id, fellowship_id=fellowship_id, creator=request.user)
    if request.method == 'POST':
        event.delete()
        cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
        return redirect('admin_my_posts_events', fellowship_id=fellowship_id)
    return render(request, 'fellowship/confirm_delete.html', {'object': event, 'type': 'event'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def donation_list_view(request):
    donations = donation.objects.all().select_related('user').order_by('-time_send')[:100]
    return render(request, 'fellowship/donation_list.html', {'donations': donations})

def fellowship_history(request):
    return render(request, 'fellowship/fellowship_history.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def accept_membership_request(request, request_id):
    req = get_object_or_404(MembershipRequest, id=request_id, accepted=False)
    FellowshipMember.objects.get_or_create(fellowship=req.fellowship, user=req.user)
    req.accepted = True
    req.save()
    
    cache.delete_pattern(f'fellowship_detail_{req.fellowship.id}_*')
    
    def send_welcome_email_async():
        try:
            user_name = req.user.get_full_name() or req.user.username
            send_mail(
                'Welcome to Bucosa Fellowship!',
                f'Dear {user_name},\n\nYour request to join {req.fellowship.name} has been accepted!\n\nWelcome to Bucosa Fellowship!\n\nYou can now login to view posts, events, and connect with other members.\n\nBest regards,\nBucosa Fellowship Team',
                settings.DEFAULT_FROM_EMAIL,
                [req.user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    Thread(target=send_welcome_email_async).start()
    
    messages.success(request, f"{req.user.username} has been accepted into the fellowship.")
    return redirect('fellowship_admin', fellowship_id=req.fellowship.id)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def membership_requests_page(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    membership_requests = MembershipRequest.objects.filter(
        fellowship=fellowship, 
        accepted=False
    ).select_related('user')
    return render(request, 'fellowship/membership_requests.html', {
        'fellowship': fellowship,
        'membership_requests': membership_requests,
    })

@require_POST
def refuse_membership_request(request, request_id):
    req = get_object_or_404(MembershipRequest, id=request_id, accepted=False)
    fellowship_id = req.fellowship.id
    req.delete()
    cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
    messages.success(request, f"{req.user.username}'s request has been refused.")
    return redirect('membership_requests_page', fellowship_id=fellowship_id)

def fellowship_events(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    events = FellowshipEvent.objects.filter(fellowship=fellowship).select_related('creator').order_by('-start_time')
    return render(request, 'fellowship/fellowship_events.html', {
        'fellowship': fellowship,
        'events': events,
    })

@login_required
@require_POST
def like_fellowship_post(request, fellowship_id, post_id):
    post = get_object_or_404(FellowshipPost, id=post_id, fellowship_id=fellowship_id)
    content_type = ContentType.objects.get_for_model(FellowshipPost)
    like, created = GenericLike.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=post.id
    )
    cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
    return redirect('fellowship_detail', fellowship_id=fellowship_id)

@login_required
@require_POST
def comment_fellowship_post(request, fellowship_id, post_id):
    post = get_object_or_404(FellowshipPost, id=post_id, fellowship_id=fellowship_id)
    content_type = ContentType.objects.get_for_model(FellowshipPost)
    content = request.POST.get('content', '').strip()
    if content:
        GenericComment.objects.create(
            content_type=content_type,
            object_id=post.id,
            author=request.user,
            content=content
        )
    cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
    return redirect('fellowship_detail', fellowship_id=fellowship_id)

@login_required
@require_POST
def share_fellowship_post(request, fellowship_id, post_id):
    post = get_object_or_404(FellowshipPost, id=post_id, fellowship_id=fellowship_id)
    content_type = ContentType.objects.get_for_model(FellowshipPost)
    GenericShare.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=post.id
    )
    cache.delete_pattern(f'fellowship_detail_{fellowship_id}_*')
    return redirect('fellowship_detail', fellowship_id=fellowship_id)

@login_required
def create_fellowship_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if not created:
        return redirect('update_fellowship_profile')
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('fellowship_profile_detail')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, "fellowship/profile.html", {'form': form})

@login_required
def update_fellowship_profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect('create_fellowship_profile')
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('fellowship_profile_detail')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, "fellowship/profile_edit.html", {'form': form})

@login_required
def fellowship_profile_detail(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, "fellowship/profile_detail.html", {'profile': profile})