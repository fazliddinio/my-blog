"""Lightweight bilingual rendering helpers.

The site supports English and Uzbek without using Django's full
``django.utils.translation`` machinery — copy is short, both languages
are first-class, and we want bodies authored straight into the database
rather than collected via ``makemessages``.

The active language is taken from the ``fz_lang`` cookie (``en`` or
``uz``) which is set by the language toggle in the header.
"""

from django import template

register = template.Library()


def _current_lang(context) -> str:
    """Return the resolved language for the current request.

    Reads ``fz_lang`` from cookies via the ``request`` in the template
    context. Falls back to English when the cookie is missing or the
    template has no request available (e.g. during email rendering).
    """
    request = context.get('request')
    if not request:
        return 'en'
    return request.COOKIES.get('fz_lang', 'en')


@register.simple_tag(takes_context=True)
def tr(context, en_text: str, uz_text: str = '') -> str:
    """Return the right-language text for a literal string.

    Usage in templates::

        {% tr "Hello" "Salom" %}

    If the Uzbek translation is missing we always fall back to English.
    """
    return uz_text if _current_lang(context) == 'uz' and uz_text else en_text


@register.filter
def bilingual(obj, field_base: str):
    """Return an attribute on ``obj`` (kept for legacy templates).

    Use :func:`bi` instead — it picks the right language automatically.
    """
    return getattr(obj, field_base, '')


@register.simple_tag(takes_context=True)
def get_lang(context) -> str:
    """Expose the current language code to templates as a variable."""
    return _current_lang(context)


@register.simple_tag(takes_context=True)
def bi(context, obj, field_base: str):
    """Pick ``{field}_{lang}`` from ``obj`` with a fallback to English.

    Usage::

        {% bi post "title" %}   {# -> post.title_uz or post.title_en #}

    This is the canonical way to render a bilingual model field; it
    avoids the historic ``data-en`` / ``data-uz`` JS-swap pattern that
    caused a flash of English content on initial load.
    """
    lang = _current_lang(context)
    value = getattr(obj, f'{field_base}_{lang}', '')
    if not value:
        # Fall back to English when the translation hasn't been written.
        value = getattr(obj, f'{field_base}_en', '')
    return value
