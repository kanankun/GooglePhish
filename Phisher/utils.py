import secrets

from django.core.cache import cache


def get_client_ip(request):
    """
    Return the client IP.

    X-Forwarded-For is trusted whenever present, which is correct only
    because this is deployed behind a reverse proxy that sets it. Exposed
    directly to the internet the header is attacker-controlled and this
    returns whatever a client claims.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def is_rate_limited(ip: str, limit: int = 10, period: int = 60) -> bool:
    """
    Simple IP-based rate limiter backed by Django's cache.
    Returns True if the IP has exceeded `limit` requests within `period` seconds.
    """
    key = f'ratelimit:signin:{ip}'
    count = cache.get(key, 0)
    if count >= limit:
        return True
    cache.set(key, count + 1, period)
    return False


def visitor_id(request):
    """A per-browser id, so one person who clicks is one row rather than
    one row per page they land on. Returned with a flag saying whether the
    caller still has to set the cookie."""
    vid = request.COOKIES.get('vid', '')
    if len(vid) == 24 and vid.isalnum():
        return vid, False
    return secrets.token_hex(12), True


def read_ua(ua: str):
    """Browser and OS, readable. Enough to fill a column."""
    ua = ua or ''
    os_name = 'Unknown'
    for needle, name in (('Windows NT 10', 'Windows 10/11'), ('Windows', 'Windows'),
                         ('iPhone', 'iPhone'), ('iPad', 'iPad'), ('Android', 'Android'),
                         ('Mac OS X', 'macOS'), ('Linux', 'Linux')):
        if needle.lower() in ua.lower():
            os_name = name
            break

    browser = 'Unknown'
    for needle, name in (('Edg', 'Edge'), ('OPR', 'Opera'),
                         ('SamsungBrowser', 'Samsung Internet'), ('Chrome', 'Chrome'),
                         ('Firefox', 'Firefox'), ('Safari', 'Safari')):
        if needle.lower() in ua.lower():
            browser = name
            break

    return browser, os_name
