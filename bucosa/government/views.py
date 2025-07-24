from django.shortcuts import render, redirect, get_object_or_404
from .models import BucosaJoinRequest, CurrentGovernment, GovernmentMember, PastGovernment
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib import messages
from django.http import HttpResponseForbidden


@login_required
def bucosa_main(request):
    user = request.user
    # Get the current government (assume latest created)
    current_gov = CurrentGovernment.objects.order_by('-created_at').first()
    gov_members = GovernmentMember.objects.filter(government=current_gov)
    # Join status for current user
    user_has_joined = BucosaJoinRequest.objects.filter(user=user, status='approved').exists()
    user_has_pending_or_approved_request = BucosaJoinRequest.objects.filter(user=user, status__in=['approved', 'pending']).exists()
    # Admin: show all join requests
    join_requests = None
    if user.is_staff:
        join_requests = BucosaJoinRequest.objects.select_related('user').all().order_by('-requested_at')
    # Handle join request POST
    if request.method == 'POST' and 'join_bucosa' in request.POST:
        if not user_has_pending_or_approved_request:
            BucosaJoinRequest.objects.create(user=user)
        return redirect('bucosa_main')
    # Handle admin actions (approve/reject)
    if request.method == 'POST' and user.is_staff and 'admin_action' in request.POST:
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(BucosaJoinRequest, id=req_id)
        if action == 'approve':
            join_request.status = 'approved'
        elif action == 'reject':
            join_request.status = 'rejected'
        join_request.reviewed_at = timezone.now()
        join_request.save()
        return redirect('bucosa_main')
    # Add past_governments to context for admin dashboard
    past_governments = PastGovernment.objects.order_by('-ended_at')
    # Add approved join requests for display
    approved_join_requests = BucosaJoinRequest.objects.filter(status='approved').select_related('user').order_by('-requested_at')
    context = {
        'current_gov': current_gov,
        'gov_members': gov_members,
        'user_has_joined': user_has_joined,
        'user_has_pending_or_approved_request': user_has_pending_or_approved_request,
        'join_requests': join_requests,
        'past_governments': past_governments,
        'approved_join_requests': approved_join_requests,
    }
    return render(request, 'government/bucosa.html', context)

@login_required
def government_history(request):
    past_governments = PastGovernment.objects.order_by('-ended_at')
    return render(request, 'government/history.html', {'past_governments': past_governments})

def redirect_to_bucosa(request):
    return redirect('bucosa_main')

def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def admin_manage_requests(request):
    join_requests = BucosaJoinRequest.objects.filter(status='pending').select_related('user')
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(BucosaJoinRequest, id=req_id)
        if action == 'approve':
            join_request.status = 'approved'
        elif action == 'reject':
            join_request.status = 'rejected'
        join_request.reviewed_at = timezone.now()
        join_request.save()
        return redirect('admin_manage_requests')
    return render(request, 'government/admin_manage_requests.html', {'join_requests': join_requests})

@user_passes_test(is_superuser)
def admin_create_current_government(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mission = request.POST.get('mission')
        image = request.FILES.get('image')
        gov = CurrentGovernment.objects.create(name=name, mission=mission, image=image)
        return redirect('bucosa_main')
    return render(request, 'government/admin_create_current_government.html')

@user_passes_test(is_superuser)
def admin_create_past_government(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mission = request.POST.get('mission')
        started_at = request.POST.get('started_at')
        ended_at = request.POST.get('ended_at')
        PastGovernment.objects.create(name=name, mission=mission, started_at=started_at, ended_at=ended_at)
        return redirect('government_history')
    return render(request, 'government/admin_create_past_government.html')

@login_required
def add_member(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    if request.method == 'POST':
        user_identifier = request.POST.get('user_identifier')
        ministry = request.POST.get('ministry')
        contact = request.POST.get('contact')
        current_gov = CurrentGovernment.objects.order_by('-created_at').first()
        user = None
        if '@' in user_identifier:
            user = User.objects.filter(email=user_identifier).first()
        else:
            user = User.objects.filter(username=user_identifier).first()
        if user and current_gov:
            GovernmentMember.objects.create(government=current_gov, user=user, ministry=ministry, contact=contact)
            messages.success(request, 'Member added successfully!')
        else:
            messages.error(request, 'User not found or no current government.')
        return redirect('bucosa_main')
    return redirect('bucosa_main')

@login_required
def edit_member(request, member_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    member = get_object_or_404(GovernmentMember, id=member_id)
    if request.method == 'POST':
        member.ministry = request.POST.get('ministry')
        member.contact = request.POST.get('contact')
        member.save()
        messages.success(request, 'Member updated successfully!')
        return redirect('bucosa_main')
    return render(request, 'government/edit_member.html', {'member': member})

@login_required
def delete_member(request, member_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    member = get_object_or_404(GovernmentMember, id=member_id)
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Member deleted successfully!')
        return redirect('bucosa_main')
    return redirect('bucosa_main')

def edit_current_government(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    current_gov = CurrentGovernment.objects.order_by('-created_at').first()
    if not current_gov:
        messages.error(request, 'No current government to edit.')
        return redirect('bucosa_main')
    if request.method == 'POST':
        current_gov.name = request.POST.get('name')
        current_gov.mission = request.POST.get('mission')
        if request.FILES.get('image'):
            current_gov.image = request.FILES['image']
        current_gov.save()
        messages.success(request, 'Current government updated!')
        return redirect('bucosa_main')
    return render(request, 'government/edit_current_government.html', {'current_gov': current_gov})

def delete_current_government(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    current_gov = CurrentGovernment.objects.order_by('-created_at').first()
    if request.method == 'POST' and current_gov:
        current_gov.delete()
        messages.success(request, 'Current government deleted!')
        return redirect('bucosa_main')
    return redirect('bucosa_main')

def edit_past_government(request, gov_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    gov = get_object_or_404(PastGovernment, id=gov_id)
    if request.method == 'POST':
        gov.name = request.POST.get('name')
        gov.mission = request.POST.get('mission')
        gov.started_at = request.POST.get('started_at')
        gov.ended_at = request.POST.get('ended_at')
        if request.FILES.get('image'):
            gov.image = request.FILES['image']
        gov.save()
        messages.success(request, 'Past government updated!')
        return redirect('bucosa_main')
    return render(request, 'government/edit_past_government.html', {'gov': gov})

def delete_past_government(request, gov_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    gov = get_object_or_404(PastGovernment, id=gov_id)
    if request.method == 'POST':
        gov.delete()
        messages.success(request, 'Past government deleted!')
        return redirect('bucosa_main')
    return redirect('bucosa_main')

def past_government_detail(request, gov_id):
    gov = get_object_or_404(PastGovernment, id=gov_id)
    members = gov.members.select_related('user').all()
    return render(request, 'government/past_government_detail.html', {
        'gov': gov,
        'members': members,
    })

def add_past_member(request, gov_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    gov = get_object_or_404(PastGovernment, id=gov_id)
    if request.method == 'POST':
        user_identifier = request.POST.get('user_identifier')
        ministry = request.POST.get('ministry')
        contact = request.POST.get('contact')
        user = None
        if '@' in user_identifier:
            user = User.objects.filter(email=user_identifier).first()
        else:
            user = User.objects.filter(username=user_identifier).first()
        if user and gov:
            from .models import PastGovernmentMember
            PastGovernmentMember.objects.create(government=gov, user=user, ministry=ministry, contact=contact)
            messages.success(request, 'Past government member added!')
        else:
            messages.error(request, 'User not found or no past government.')
        return redirect('past_government_detail', gov_id=gov.id)
    return redirect('past_government_detail', gov_id=gov.id)

def edit_past_member(request, member_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    from .models import PastGovernmentMember
    member = get_object_or_404(PastGovernmentMember, id=member_id)
    if request.method == 'POST':
        member.ministry = request.POST.get('ministry')
        member.contact = request.POST.get('contact')
        member.save()
        messages.success(request, 'Past government member updated!')
        return redirect('past_government_detail', gov_id=member.government.id)
    return render(request, 'government/edit_past_member.html', {'member': member})

def delete_past_member(request, member_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    from .models import PastGovernmentMember
    member = get_object_or_404(PastGovernmentMember, id=member_id)
    gov_id = member.government.id
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Past government member deleted!')
        return redirect('past_government_detail', gov_id=gov_id)
    return redirect('past_government_detail', gov_id=gov_id)