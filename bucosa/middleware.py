from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
import re

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        # Build EXEMPT_URLS at request time to avoid reverse() import errors
        exempt_urls = [
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
        if not request.user.is_authenticated:
            if not any(m.match(path) for m in exempt_urls):
                return redirect(settings.LOGIN_URL + f'?next={request.path}')
        return self.get_response(request)
