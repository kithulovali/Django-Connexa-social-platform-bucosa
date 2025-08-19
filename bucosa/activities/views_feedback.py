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
            return redirect('users:profile')
    else:
        form = FeedbackForm()
    return render(request, 'activities/feedback.html', {'form': form})
