from allauth.account.signals import user_signed_up
from activities.models import Post
import logging
from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(user_signed_up)
def create_default_post_on_social_signup(request, user, **kwargs):
    # Try to get extra data from social account
    try:
        social = SocialAccount.objects.filter(user=user).first()
        if social:
            extra = social.extra_data
            if extra.get('given_name'):
                user.first_name = extra['given_name']
            if extra.get('family_name'):
                user.last_name = extra['family_name']
            if extra.get('email'):
                user.email = extra['email']
            user.save()
    except Exception:
        pass
    # Compose welcome name
    if user.first_name or user.last_name:
        welcome_name = f"{user.first_name} {user.last_name}".strip()
    elif user.email:
        welcome_name = user.email
    else:
        welcome_name = user.username
    try:
        post = Post.objects.create(
            author=user,
            content=f"🌟🌟✨✨ Welcome {welcome_name} to Bucosa! We're excited to have you join our community. Feel free to explore, connect, and share your first post!",
            privacy="PRIVATE",
            is_welcome_post=True
        )
        logger = logging.getLogger(__name__)
        logger.info(f"Welcome post created for new social user {user.username} (post id: {post.id})")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create welcome post for new social user {user.username}: {e}")


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
