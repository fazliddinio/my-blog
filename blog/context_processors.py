"""Context processors for the blog app.

These run on every template render and expose a handful of values that
nearly every template needs (site settings, current language, etc.) so
individual views don't have to remember to pass them in.
"""

from django.conf import settings

from blog.models import SiteSettings


def site_settings(request):
    """Expose the cached :class:`~blog.models.SiteSettings` row.

    Cached so the read is essentially free even though it's hit on every
    page render.
    """
    return {'site_settings': SiteSettings.cached()}


def user_lang(request):
    """Expose the resolved language and a couple of convenience flags.

    ``LANG`` is a two-letter code (``"en"`` or ``"uz"``).  ``IS_UZ`` is a
    boolean shortcut for the common ``{% if LANG == 'uz' %}`` check.
    ``DEFAULT_OG_IMAGE`` is here so templates can use a single fallback
    image when a post has no featured image of its own.
    """
    lang = getattr(request, 'lang', 'en')
    return {
        'LANG': lang,
        'IS_UZ': lang == 'uz',
        'DEFAULT_OG_IMAGE': getattr(settings, 'SITE_DEFAULT_OG_IMAGE', ''),
    }
