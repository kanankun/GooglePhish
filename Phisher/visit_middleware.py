"""Record that somebody opened the page, before they type anything.

Done as middleware rather than inside the views, so the landing pages stay
byte-identical to upstream and a pull cannot quietly drop this.

Only ordinary page views count: HTML GETs that are not the dashboard, the
beacon, the admin or a static file.
"""
from django.db.models import F
from django.utils import timezone

from .models import Visit
from .utils import get_client_ip, visitor_id, read_ua

SKIP_PREFIXES = ('/collect', '/pawned', '/ops-', '/static', '/get-hits', '/favicon')


class VisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        vid, is_new = visitor_id(request)
        request.vid = vid

        response = self.get_response(request)

        if not self._interesting(request, response):
            return response

        if not is_new:
            # Same browser, another page load. Count it, but do not add a
            # second person to the total.
            Visit.objects.filter(vid=vid).update(
                hits=F('hits') + 1, last_seen=timezone.now())
            return response

        browser, os_name = read_ua(request.META.get('HTTP_USER_AGENT', ''))
        try:
            Visit.objects.create(
                vid=vid,
                client_ip=get_client_ip(request) or '',
                browser=browser,
                os=os_name,
                language=request.META.get('HTTP_ACCEPT_LANGUAGE', '')[:120],
                referer=request.META.get('HTTP_REFERER', '')[:300],
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception:
            return response          # never break a page over telemetry

        response.set_cookie('vid', vid, max_age=3600, samesite='Lax')
        return response

    @staticmethod
    def _interesting(request, response):
        if request.method != 'GET':
            return False
        path = request.path or '/'
        if path.startswith(SKIP_PREFIXES):
            return False
        return 'text/html' in response.get('Content-Type', '')
