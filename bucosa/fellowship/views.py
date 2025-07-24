from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from . forms import  donationForm , fellowship_editForm
from . models import fellowship_edit , donation , FellowshipMember , FellowshipPost , FellowshipEvent
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

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
    FellowshipMember.objects.get_or_create(fellowship=fellowship, user=request.user)
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
            post = FellowshipPost.objects.create(fellowship=fellowship, author=request.user, content=content, image=image, video=video)
            from fellowship.models import FellowshipMember
            from notifications.models import Notification
            members = FellowshipMember.objects.filter(fellowship=fellowship).exclude(user=request.user)
            for member in members:
                notification = Notification.objects.create(
                    sender=request.user,
                    recipient=member.user,
                    notification_type='other',
                    message=f'New post in {fellowship.name}.'
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
            from fellowship.models import FellowshipMember
            from notifications.models import Notification
            members = FellowshipMember.objects.filter(fellowship=fellowship).exclude(user=request.user)
            for member in members:
                notification = Notification.objects.create(
                    sender=request.user,
                    recipient=member.user,
                    notification_type='other',
                    message=f'New event "{event.title}" in {fellowship.name}.'
                )
    return render(request, 'fellowship/create_event.html', {'fellowship': fellowship})

@login_required
def fellowship_detail(request, fellowship_id):
    fellowship = get_object_or_404(fellowship_edit, id=fellowship_id)
    posts = FellowshipPost.objects.filter(fellowship=fellowship).order_by('-created_at')
    events = FellowshipEvent.objects.filter(fellowship=fellowship).order_by('-start_time')
    members = FellowshipMember.objects.filter(fellowship=fellowship)
    is_member = members.filter(user=request.user).exists()
    is_admin = fellowship.admin == request.user
    followers_count = members.count()
    return render(request, 'fellowship/fellowship_detail.html', {
        'fellowship': fellowship,
        'posts': posts,
        'events': events,
        'members': members,
        'is_member': is_member,
        'is_admin': is_admin,
        'followers_count': followers_count,
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
    return render(request, 'fellowship/fellowship_admin.html', {
        'fellowship': fellowship,
        'members': members,
        'posts': posts,
        'events': events,
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