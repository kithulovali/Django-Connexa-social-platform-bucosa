from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from .forms_feedback import FeedbackForm
from .models_feedback import Feedback
from users.models_private_message import PrivateMessage

@login_required
def send_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()

            # Send message to goffart
            User = get_user_model()
            try:
                receiver = User.objects.get(username=settings.FEEDBACK_RECEIVER_USERNAME)
                # Get sender's name and profile image
                sender_profile = getattr(request.user, 'profile', None)
                sender_name = request.user.get_full_name() or request.user.username
                profile_image_url = ''
                if sender_profile and hasattr(sender_profile, 'profile_image') and sender_profile.profile_image:
                    profile_image_url = sender_profile.profile_image.url
                feedback_content = f"[Feedback from {sender_name}]\nMessage: {feedback.message}"
                if profile_image_url:
                    feedback_content += f"\nProfile Image: {profile_image_url}"
                PrivateMessage.objects.create(
                    sender=request.user,
                    recipient=receiver,
                    content=feedback_content
                )
            except User.DoesNotExist:
                pass

            messages.success(request, 'Thank you for your feedback!')
            return redirect('activities:feedback')
    else:
        form = FeedbackForm()
    return render(request, 'activities/feedback.html', {'form': form})
