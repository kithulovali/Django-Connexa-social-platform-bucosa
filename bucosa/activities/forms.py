from django import forms
from .models import Post, Event, Comment
from django.contrib.auth.models import Group

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_size(image):
    if image and image.size > MAX_IMAGE_SIZE:
        raise forms.ValidationError("Image file too large (max 10MB).")
    return image
class PostForm(forms.ModelForm):
    group = forms.ModelChoiceField(queryset=Group.objects.none(), required=False, help_text="(Optional) Post to a group you belong to.")
    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'group']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['group'].queryset = Group.objects.filter(user=user)
        if group:
            self.fields['group'].initial = group.id
            self.fields['group'].disabled = True
    def clean_image(self):
        image = self.cleaned_data.get('image')
        return validate_image_size(image)

class EventForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True
    )
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time', 'cover_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        return validate_image_size(image)

class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].widget = forms.HiddenInput()

    class Meta:
        model = Comment
        fields = ['content', 'parent']
