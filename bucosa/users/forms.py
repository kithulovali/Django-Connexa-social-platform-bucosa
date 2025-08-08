from .models import user_profile, GroupProfile
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import Group

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_size(image):
    if image and image.size > MAX_IMAGE_SIZE:
        raise forms.ValidationError("Image file too large (max 10MB).")
    return image

class profileForm(ModelForm):
    class Meta:
        model = user_profile
        exclude = ['user']

class GroupCreateForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, required=True)
    class Meta:
        model = Group
        fields = ['name', 'description']

class GroupProfileForm(forms.ModelForm):
    class Meta:
        model = GroupProfile
        fields = ['profile_image']
        
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        return validate_image_size(image)

class ProfileUpdateForm(ModelForm):
    username = forms.CharField(max_length=150, required=True, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.")
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    class Meta:
        model = user_profile
        fields = ['username', 'first_name', 'last_name', 'email', 'bio', 'profile_image', 'location']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image is None:  # If no file was uploaded
             return self.instance.profile_image  # Keep the existing image
        return validate_image_size(image)

    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        return validate_image_size(image)
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.username = self.cleaned_data.get('username', user.username)
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        if commit:
            user.save()
            profile.save()
        return profile