from allauth.account.adapter import DefaultAccountAdapter
from django.utils.crypto import get_random_string

class CustomAccountAdapter(DefaultAccountAdapter):
    def generate_unique_username(self, txts, regex=None):
        # Always generate a random username for social logins
        return get_random_string(16)

    def populate_username(self, request, user):
        # Always set a random username for new users
        user.username = get_random_string(16)
