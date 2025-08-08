from .models import user_profile, GroupProfile
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_size(image):
    """Validate image size with proper error handling"""
    if not image:
        return None
        
    if not hasattr(image, 'size'):
        raise ValidationError("Invalid image file provided")
        
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError(f"Image file too large (max {MAX_IMAGE_SIZE//(1024*1024)}MB)")
    return image

class ProfileForm(ModelForm):
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
        if image is None:  # If field was cleared
            return self.instance.profile_image if hasattr(self.instance, 'profile_image') else None
        return validate_image_size(image)

class ProfileUpdateForm(ModelForm):
    username = forms.CharField(
        max_length=150, 
        required=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)  # Added email field explicitly
    
    class Meta:
        model = user_profile
        fields = ['username', 'first_name', 'last_name', 'email', 'bio', 'profile_image', 'location']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        # Return existing image if no new one was uploaded
        if image is None:
            return getattr(self.instance, 'profile_image', None)
        return validate_image_size(image)
    
    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if image is None:
            return getattr(self.instance, 'cover_image', None)
        return validate_image_size(image)
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if hasattr(profile, 'user'):
            user = profile.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if commit:
                user.save()
        if commit:
            profile.save()
        return profile