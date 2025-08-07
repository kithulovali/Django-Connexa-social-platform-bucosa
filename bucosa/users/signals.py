from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(social_account_added)
def sync_google_profile_on_add(request, sociallogin, **kwargs):
    if sociallogin.account.provider == 'google':
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data
        # Sync name
        user.first_name = extra_data.get('given_name', user.first_name)
        user.last_name = extra_data.get('family_name', user.last_name)
        # Sync email (should already be set)
        user.email = extra_data.get('email', user.email)
        
        # Sync avatar/profile picture - safely handle profile creation
        try:
            if hasattr(user, 'profile') and user.profile:
                user.profile.avatar_url = extra_data.get('picture', getattr(user.profile, 'avatar_url', ''))
                user.profile.save(update_fields=['avatar_url'])
        except Exception:
            # Profile doesn't exist or other error - ignore for now
            # Profile will be created when needed by other views
            pass
        user.save()

@receiver(social_account_updated)
def sync_google_profile_on_update(request, sociallogin, **kwargs):
    if sociallogin.account.provider == 'google':
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data
        user.first_name = extra_data.get('given_name', user.first_name)
        user.last_name = extra_data.get('family_name', user.last_name)
        user.email = extra_data.get('email', user.email)
        
        # Sync avatar/profile picture - safely handle profile access
        try:
            if hasattr(user, 'profile') and user.profile:
                user.profile.avatar_url = extra_data.get('picture', getattr(user.profile, 'avatar_url', ''))
                user.profile.save(update_fields=['avatar_url'])
        except Exception:
            # Profile doesn't exist or other error - ignore for now
            # Profile will be created when needed by other views
            pass
        user.save()
