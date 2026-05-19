"""Custom middleware for the public site."""


class LanguageCookieMiddleware:
    """Attach a normalised ``request.lang`` to every request.

    The site uses an ``fz_lang`` cookie set client-side by the language
    toggle. Reading it once here means views and templates can rely on
    ``request.lang`` instead of re-reading ``request.COOKIES`` (and
    re-validating the value) everywhere.

    Unknown values fall back to English so a tampered cookie can't put
    the site into an unsupported state.
    """

    SUPPORTED = {'en', 'uz'}

    def __init__(self, get_response):
        # Standard Django middleware constructor: store the next handler
        # in the chain so ``__call__`` can hand the request off.
        self.get_response = get_response

    def __call__(self, request):
        raw = (request.COOKIES.get('fz_lang') or 'en').lower()
        request.lang = raw if raw in self.SUPPORTED else 'en'
        return self.get_response(request)
