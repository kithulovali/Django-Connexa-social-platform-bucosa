from django.contrib.contenttypes.models import ContentType
from activities.models import GenericLike, GenericComment, GenericShare
from django.contrib.auth.decorators import login_required
from .models import MembershipRequest
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from . forms import  donationForm , fellowship_editForm , ProfileForm
from . models import fellowship_edit , donation , FellowshipMember , FellowshipPost , FellowshipEvent , Profile
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import Notification
from django.contrib.auth.models import User
from fellowship.models import FellowshipMember
from activities.models import GenericLike, GenericComment
from django.contrib.contenttypes.models import ContentType
# Create your views here.
@login_required
def fellowship_view(request):
    edit = fellowship_edit.objects.all()
    context ={
        'edit':edit
    }
    return render(request , 'fellowship/fellowship.html' , context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_fellowship(request, fellowship_id):
    fellowship_instance = get_object_or_404(fellowship_edit, id=fellowship_id)
    if request.method == 'POST':
        form = fellowship_editForm(request.POST, request.FILES, instance=fellowship_instance)
        if form.is_valid():
            form.save()
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
            return redirect('fellowship_detail', fellowship_id=fellowship_id)
    else:
        form = fellowship_editForm(instance=fellowship_instance)
    context = {
        'form': form,
        'fellowship': fellowship_instance
    }
    return render(request, 'fellowship/edit_fellowship_model.html', context)

def  donate_view(request):
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
    from .models import MembershipRequest, FellowshipMember
    if not FellowshipMember.objects.filter(fellowship=fellowship, user=request.user).exists():
        if not MembershipRequest.objects.filter(fellowship=fellowship, user=request.user, accepted=False).exists():
            MembershipRequest.objects.create(fellowship=fellowship, user=request.user)
            messages.success(request, "Your request to join has been sent to the admin.")
        else:
            messages.info(request, "You have already requested to join.")
    else:
        messages.info(request, "You are already a member.")
    return redirect('fellowship_detail', fellowship_id=fellowship.id)

def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated_view_func

@superuser_required
def create_fellowship_post(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        if content:
            FellowshipPost.objects.create(
                fellowship=fellowship,
                author=request.user,
                content=content,
                image=image,
                video=video
            )
            members = FellowshipMember.objects.filter(fellowship=fellowship).exclude(user=request.user)
            for member in members:
                Notification.objects.create(
                    sender=request.user,
                    recipient=member.user,
                    notification_type='other',
                    message=f'New post in {fellowship.name}.'
                )
            # Email all users with an email address (except the creator)
            all_users = User.objects.exclude(id=request.user.id).exclude(email='').exclude(email__isnull=True)
            site_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
            fellowship_url = request.build_absolute_uri(f'/fellowship/{fellowship.id}/')
            for user in all_users:
                send_mail(
                    'Bucosa Fellowship Posted',
                    f'{request.user.username} posted in {fellowship.name}:\n\n{content}\n\nView on site: {fellowship_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
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
            
            members = FellowshipMember.objects.filter(fellowship=fellowship).exclude(user=request.user)
            for member in members:
                Notification.objects.create(
                    sender=request.user,
                    recipient=member.user,
                    notification_type='other',
                    message=f'New event "{event.title}" in {fellowship.name}.'
                )
            # Email all users with an email address (except the creator)
            all_users = User.objects.exclude(id=request.user.id).exclude(email='').exclude(email__isnull=True)
            site_url = request.build_absolute_uri('/')[:-1]
            fellowship_url = request.build_absolute_uri(f'/fellowship/{fellowship.id}/')
            for user in all_users:
                send_mail(
                    'Join the Fellowship Event',
                    f'{request.user.username} created an event in {fellowship.name}: {title}\n\nDescription: {description}\nLocation: {location}\nStart: {start_time}\nEnd: {end_time}\n\nJoin or view event: {fellowship_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
    return render(request, 'fellowship/create_event.html', {'fellowship': fellowship})

@login_required
def fellowship_detail(request, fellowship_id):
    try:
        profile_fellowship = fellowship.fellowship_profile
    except fellowship_edit.DoesNotExist:
        profile_fellowship = None
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    posts = FellowshipPost.objects.filter(fellowship=fellowship, author=fellowship.admin).order_by('-created_at')
    events = FellowshipEvent.objects.filter(fellowship=fellowship).order_by('-start_time')
    members = FellowshipMember.objects.filter(fellowship=fellowship)
    is_member = members.filter(user=request.user).exists()
    is_admin = fellowship.admin == request.user
    followers_count = members.count()

    # Annotate posts with like_count, comment_count, and comments

    post_ct = ContentType.objects.get_for_model(FellowshipPost)
    annotated_posts = []
    for post in posts:
        like_count = GenericLike.objects.filter(content_type=post_ct, object_id=post.id).count()
        comment_qs = GenericComment.objects.filter(content_type=post_ct, object_id=post.id).order_by('created_at')
        comment_count = comment_qs.count()
        comments = list(comment_qs)
        # Optionally, you can annotate if the user has liked/shared
        post.like_count = like_count
        post.comment_count = comment_count
        post.comments = comments
        annotated_posts.append(post)

    return render(request, 'fellowship/fellowship_detail.html', {
        'fellowship': fellowship,
        'fellowship_posts': annotated_posts,
        'events': events,
        'members': members,
        'is_member': is_member,
        'is_admin': is_admin,
        'followers_count': followers_count,
        'profile_fellowship': profile_fellowship,
    })

@login_required
def fellowship_admin_dashboard(request, fellowship_id):
    try:
        fellowship = fellowship_edit.objects.get(id=fellowship_id)
    except fellowship_edit.DoesNotExist:
        if request.user.is_superuser:
            # Auto-create a fellowship for superusers if missing
            fellowship = fellowship_edit.objects.create(
                id=fellowship_id,
                name='Main Fellowship',
                email=request.user.email or 'admin@example.com',
                admin=request.user
            )
            messages.success(request, 'Default fellowship created.')
        else:
            messages.error(request, 'Fellowship not found.')
            return redirect('fellowship')
    if fellowship.admin != request.user and not request.user.is_superuser:
        return redirect('fellowship_detail', fellowship_id=fellowship.id)
    members = FellowshipMember.objects.filter(fellowship=fellowship)
    posts = FellowshipPost.objects.filter(fellowship=fellowship)
    events = FellowshipEvent.objects.filter(fellowship=fellowship)
    from .models import MembershipRequest
    membership_requests = MembershipRequest.objects.filter(fellowship=fellowship, accepted=False)
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
    posts = FellowshipPost.objects.filter(fellowship=fellowship, author=request.user)
    events = FellowshipEvent.objects.filter(fellowship=fellowship, creator=request.user)
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
        return redirect('admin_my_posts_events', fellowship_id=fellowship_id)
    return render(request, 'fellowship/confirm_delete.html', {'object': event, 'type': 'event'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def donation_list_view(request):
    donations = donation.objects.all().order_by('-time_send')
    return render(request, 'fellowship/donation_list.html', {'donations': donations})

def fellowship_history(request):
    
    return render(request, 'fellowship/fellowship_history.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def accept_membership_request(request, request_id):
    from .models import MembershipRequest, FellowshipMember
    req = get_object_or_404(MembershipRequest, id=request_id, accepted=False)
    FellowshipMember.objects.get_or_create(fellowship=req.fellowship, user=req.user)
    req.accepted = True
    req.save()
    # Send welcome email to the user
    from django.core.mail import send_mail
    from django.conf import settings
    user_name = req.user.get_full_name() or req.user.username
    send_mail(
        'Welcome to Bucosa Fellowship!',
        f'Dear {user_name},\n\nYour request to join {req.fellowship.name} has been accepted!\n\nWelcome to Bucosa Fellowship!\n\nYou can now login to view posts, events, and connect with other members.\n\nBest regards,\nBucosa Fellowship Team',
        settings.DEFAULT_FROM_EMAIL,
        [req.user.email],
        fail_silently=True,
    )
    messages.success(request, f"{req.user.username} has been accepted into the fellowship.")
    return redirect('fellowship_admin', fellowship_id=req.fellowship.id)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def membership_requests_page(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    membership_requests = MembershipRequest.objects.filter(fellowship=fellowship, accepted=False)
    return render(request, 'fellowship/membership_requests.html', {
        'fellowship': fellowship,
        'membership_requests': membership_requests,
    })
@require_POST
def refuse_membership_request(request, request_id):
    from .models import MembershipRequest
    req = get_object_or_404(MembershipRequest, id=request_id, accepted=False)
    req.delete()
    messages.success(request, f"{req.user.username}'s request has been refused.")
    return redirect('membership_requests_page', fellowship_id=req.fellowship.id)
def fellowship_events(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    events = FellowshipEvent.objects.filter(fellowship=fellowship).order_by('-start_time')
    return render(request, 'fellowship/fellowship_events.html', {
        'fellowship': fellowship,
        'events': events,
    })
    # Like FellowshipPost
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
    return redirect('fellowship_detail', fellowship_id=fellowship_id)

# Comment FellowshipPost
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
    return redirect('fellowship_detail', fellowship_id=fellowship_id)

# Share FellowshipPost
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
    return redirect('fellowship_detail', fellowship_id=fellowship_id)

@login_required
def create_fellowship_profile(request):
    # Check if user already has a profile
    if hasattr(request.user, 'fellowship_profile'):
        return redirect('update_fellowship_profile')
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return redirect('fellowship_profile_detail')
    else:
        form = ProfileForm()
    
    return render(request, "fellowship/profile.html", {
        'form': form
    })
    
@login_required
def update_fellowship_profile(request):
    # Get the user's profile or return 404 if it doesn't exist
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('fellowship_profile_detail')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, "fellowship/profile_edit.html", {
        'form': form
    })

@login_required
def fellowship_profile_detail(request):
    # Get the user's profile or return 404 if it doesn't exist
    profile = get_object_or_404(Profile, user=request.user)
    
    return render(request, "fellowship/profile_detail.html", {
        'profile': profile
    })