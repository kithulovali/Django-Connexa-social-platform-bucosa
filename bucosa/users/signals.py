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
    # Only update fields if changed, and use update_fields for efficiency
    try:
        social = SocialAccount.objects.filter(user=user).first()
        update_fields = []
        if social:
            extra = social.extra_data
            if extra.get('given_name') and user.first_name != extra['given_name']:
                user.first_name = extra['given_name']
                update_fields.append('first_name')
            if extra.get('family_name') and user.last_name != extra['family_name']:
                user.last_name = extra['family_name']
                update_fields.append('last_name')
            if extra.get('email') and user.email != extra['email']:
                user.email = extra['email']
                update_fields.append('email')
            if update_fields:
                user.save(update_fields=update_fields)
    except Exception:
        pass
    # Compose welcome name
    if user.first_name or user.last_name:
        welcome_name = f"{user.first_name} {user.last_name}".strip()
    elif user.email:
        welcome_name = user.email
    else:
        welcome_name = user.username
    # Only create welcome post if not already present
    try:
        if not Post.objects.filter(author=user, is_welcome_post=True).exists():
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
        update_fields = []
        if extra_data.get('given_name') and user.first_name != extra_data.get('given_name'):
            user.first_name = extra_data.get('given_name')
            update_fields.append('first_name')
        if extra_data.get('family_name') and user.last_name != extra_data.get('family_name'):
            user.last_name = extra_data.get('family_name')
            update_fields.append('last_name')
        if extra_data.get('email') and user.email != extra_data.get('email'):
            user.email = extra_data.get('email')
            update_fields.append('email')
        # Sync avatar/profile picture - safely handle profile creation
        try:
            if hasattr(user, 'profile') and user.profile:
                avatar_url = extra_data.get('picture', getattr(user.profile, 'avatar_url', ''))
                if user.profile.avatar_url != avatar_url:
                    user.profile.avatar_url = avatar_url
                    user.profile.save(update_fields=['avatar_url'])
        except Exception:
            pass
        if update_fields:
            user.save(update_fields=update_fields)

@receiver(social_account_updated)
def sync_google_profile_on_update(request, sociallogin, **kwargs):
    if sociallogin.account.provider == 'google':
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data
        update_fields = []
        if extra_data.get('given_name') and user.first_name != extra_data.get('given_name'):
            user.first_name = extra_data.get('given_name')
            update_fields.append('first_name')
        if extra_data.get('family_name') and user.last_name != extra_data.get('family_name'):
            user.last_name = extra_data.get('family_name')
            update_fields.append('last_name')
        if extra_data.get('email') and user.email != extra_data.get('email'):
            user.email = extra_data.get('email')
            update_fields.append('email')
        # Sync avatar/profile picture - safely handle profile access
        try:
            if hasattr(user, 'profile') and user.profile:
                avatar_url = extra_data.get('picture', getattr(user.profile, 'avatar_url', ''))
                if user.profile.avatar_url != avatar_url:
                    user.profile.avatar_url = avatar_url
                    user.profile.save(update_fields=['avatar_url'])
        except Exception:
            pass
        if update_fields:
            user.save(update_fields=update_fields)
