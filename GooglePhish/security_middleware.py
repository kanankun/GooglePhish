"""
VULN-6 fix: inject missing security headers on every response.
"""


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Prevent loading resources from untrusted origins
        response.setdefault(
            'Content-Security-Policy',
            "default-src 'self'; "
            "script-src 'self'; "
            # The font and the favicon are served from here now, so
            # nothing needs an exception and the page makes no request to
            # anyone else. Fewer moving parts on a bad wifi connection,
            # and nothing in a defender's DNS log either.
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';",
        )

        # Enforce HTTPS for 1 year (only meaningful when served over TLS)
        response.setdefault(
            'Strict-Transport-Security',
            'max-age=31536000; includeSubDomains',
        )

        # Restrict browser feature access
        response.setdefault(
            'Permissions-Policy',
            'geolocation=(), microphone=(), camera=()',
        )

        # Never cache pages that may contain sensitive form state
        response.setdefault(
            'Cache-Control',
            'no-store, no-cache, must-revalidate, max-age=0',
        )
        response.setdefault('Pragma', 'no-cache')

        return response
