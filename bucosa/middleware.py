from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only redirect if not authenticated and not accessing exempt URLs
        exempt_urls = getattr(settings, 'LOGIN_EXEMPT_URLS', [reverse('account_login'), reverse('account_signup')])
        if not request.user.is_authenticated and request.path not in exempt_urls:
            return redirect(settings.LOGIN_URL)
        return self.get_response(request)
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
import re

EXEMPT_URLS = [
    re.compile(reverse('users:login').lstrip('/')),
    re.compile(reverse('users:logout').lstrip('/')),
    re.compile(reverse('users:register').lstrip('/')),
    re.compile(r'^admin/'),
    re.compile(r'^accounts/'),
    re.compile(r'^static/'),
    re.compile(r'^media/'),
    re.compile(r'^manifest.json$'),
    re.compile(r'^service-worker.js$'),
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        if not request.user.is_authenticated:
            if not any(m.match(path) for m in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL + f'?next={request.path}')
        return self.get_response(request)
