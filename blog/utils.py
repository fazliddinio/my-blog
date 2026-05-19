"""Utility helpers shared across the blog app.

Grouped roughly by responsibility:

* **Rendering** — Markdown ↔ HTML, table-of-contents extraction,
  heading-id injection, read-time estimation.
* **Image optimisation** — resize/re-encode uploads via Pillow.
* **Email** — small wrappers around ``django.core.mail`` that always log
  failures (we never silently swallow them in production).
* **Security** — safe redirect helper (open-redirect proof), per-IP
  rate-limit decorator, honeypot probe.

Nothing here is HTTP-aware (apart from the few helpers that explicitly
take a ``request``); everything is unit-testable in isolation.
"""

from __future__ import annotations

import logging
import re
import secrets
from functools import wraps
from io import BytesIO
from urllib.parse import urlparse

import markdown
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

try:
    from PIL import Image
except ImportError:  # pragma: no cover -- Pillow is in requirements.txt
    Image = None

logger = logging.getLogger('blog')


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

# Matches an ``<h2>`` or ``<h3>`` tag, optionally with attributes, and captures
# its inner HTML. Used by the TOC extractor and the heading-id injector.
_HEADING_RE = re.compile(r'<h([23])([^>]*)>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)

# A body containing any of these block-level HTML tags is almost certainly
# author-written HTML, not Markdown. We use this as a guard to avoid
# accidentally promoting an HTML body to Markdown via :func:`looks_like_markdown`.
_BLOCK_HTML_RE = re.compile(
    r'</?(?:p|div|article|section|ul|ol|li|h[1-6]|pre|code|table|figure|blockquote|img|hr)\b',
    re.IGNORECASE,
)

# Block-level Markdown markers anchored to the start of a line.
# (Inline markers like ``**bold**`` are not enough on their own — they
# also occur in HTML and would produce false positives.)
_MD_MARKER_RE = re.compile(r'(?m)^(?:#{1,6}\s|[*\-]\s|\d+\.\s|>\s|```|~~~)')


def looks_like_markdown(text: str) -> bool:
    """Heuristic: would this body render correctly as Markdown?

    Used to auto-fix posts that were stored with ``content_format='html'``
    but whose body is actually Markdown (a common copy-paste mistake).

    The check is intentionally conservative — it returns ``True`` only when
    the body has Markdown markers *and* no block-level HTML tags.
    """
    if not text:
        return False
    if _BLOCK_HTML_RE.search(text):
        return False
    return bool(_MD_MARKER_RE.search(text))


def estimate_read_time(text: str) -> int:
    """Return an estimated reading time in minutes.

    Uses 200 words-per-minute, the figure most studies converge on for
    online prose. Anything below a minute is rounded up to one.
    """
    words = len(strip_tags(text or '').split())
    return max(1, words // 200)


def render_content(raw: str, content_format: str) -> str:
    """Render a post / issue body into safe HTML.

    Markdown is run through :mod:`python-markdown` with the extensions we
    care about (fenced code, tables, line breaks, lists, TOC). HTML is
    passed through verbatim — bodies are author-controlled, not user
    input, so we don't need a sanitiser like ``bleach``.
    """
    if not raw:
        return ''
    if content_format == 'markdown':
        return markdown.markdown(
            raw,
            extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists', 'toc'],
            output_format='html5',
        )
    return raw


def _slugify_id(value: str) -> str:
    """Turn arbitrary heading text into a URL-safe ``id`` attribute."""
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-') or 'section'


def inject_heading_ids(html: str) -> str:
    """Add stable ``id`` attributes to every ``<h2>`` / ``<h3>`` heading.

    Existing ``id`` attributes are preserved so authors can override the
    auto-generated value when they need a stable anchor (e.g. for inbound
    links from older posts).
    """

    def replacer(match: re.Match) -> str:
        level = match.group(1)
        attrs = match.group(2) or ''
        inner = match.group(3)
        # Author-supplied id wins.
        existing = re.search(r'id="([^"]*)"', attrs)
        if existing:
            return match.group(0)
        anchor = _slugify_id(strip_tags(inner).strip())
        return f'<h{level}{attrs} id="{anchor}">{inner}</h{level}>'

    return _HEADING_RE.sub(replacer, html or '')


def extract_toc(html: str) -> list[dict]:
    """Return a list of ``{level, id, title}`` entries for the page's TOC.

    Only ``<h2>`` and ``<h3>`` are included — ``<h1>`` is the post title,
    and deeper headings are usually noise in a TOC.
    """
    toc: list[dict] = []
    for match in _HEADING_RE.finditer(html or ''):
        level = int(match.group(1))
        attrs = match.group(2) or ''
        inner = match.group(3)
        title = strip_tags(inner).strip()
        if not title:
            continue
        existing = re.search(r'id="([^"]*)"', attrs)
        anchor = existing.group(1) if existing else _slugify_id(title)
        toc.append({'level': level, 'id': anchor, 'title': title})
    return toc


# ---------------------------------------------------------------------------
# Image optimisation
# ---------------------------------------------------------------------------


def optimize_image_field(image_field, max_width: int = 1600) -> None:
    """Resize/recompress an uploaded image so we don't ship 5 MB hero PNGs.

    No-op when Pillow isn't available (we still want the rest of the
    request to succeed) or when the file can't be opened (corrupt
    upload, wrong content-type, …). Anything wider than ``max_width`` is
    scaled down keeping the aspect ratio; everything is re-encoded as
    JPEG at quality 85 (the sweet spot between size and visual fidelity).
    """
    if not Image or not image_field:
        return

    try:
        image_field.open()
        img = Image.open(image_field)
    except Exception as exc:  # pragma: no cover
        logger.warning('Could not open uploaded image: %s', exc)
        return

    try:
        # JPEG can't represent alpha or palette images; convert first.
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize(
                (max_width, int(img.height * ratio)),
                Image.Resampling.LANCZOS,
            )

        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        new_name = (image_field.name.rsplit('.', 1)[0] or 'image') + '.jpg'
        image_field.save(new_name, BytesIO(buffer.getvalue()), save=False)
    except Exception as exc:  # pragma: no cover
        logger.warning('Image optimisation failed: %s', exc)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------


def site_base_url() -> str:
    """Absolute base URL of the site, sourced from ``SiteSettings``.

    Used wherever we need to build a fully-qualified URL outside the
    request/response cycle (e.g. inside an outgoing email).
    """
    # Local import: ``models`` imports from this module, breaking a top-level
    # import chain.
    from blog.models import SiteSettings
    return SiteSettings.cached().site_url.rstrip('/')


def send_site_email(subject: str, template: str, context: dict, to: list[str]) -> bool:
    """Render ``template`` with ``context`` and send the resulting HTML email.

    Returns ``True`` on success and ``False`` (without raising) when the
    underlying SMTP call fails. We log every failure with the recipient
    list so production issues are debuggable from gunicorn logs alone.
    """
    if not to or not settings.DEFAULT_FROM_EMAIL:
        return False
    try:
        html = render_to_string(template, context)
        send_mail(
            subject=subject,
            # Plain-text fallback for clients that don't render HTML.
            message=strip_tags(html),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=to,
            html_message=html,
            # Never silently swallow errors in production — we log them.
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.warning('Email send failed (%s -> %s): %s', subject, to, exc)
        return False


def send_contact_notification(message) -> None:
    """Notify the site owner that a new contact message has arrived."""
    notify = getattr(settings, 'CONTACT_NOTIFY_EMAIL', '')
    if not notify:
        # Notifications are opt-in; if no recipient is configured we just
        # store the message and rely on the dashboard for triage.
        return
    send_site_email(
        subject=f'New contact message from {message.email}',
        template='email/contact_notification.html',
        context={'message': message, 'site_url': site_base_url()},
        to=[notify],
    )


def send_subscriber_confirmation(subscriber) -> None:
    """Send the double-opt-in confirmation email to a fresh subscriber."""
    confirm_url = (
        f'{site_base_url()}'
        f'{reverse("blog:confirm_subscription", args=[subscriber.confirm_token])}'
    )
    send_site_email(
        subject='Confirm your subscription — fazliddin.com',
        template='email/confirm_subscription.html',
        context={'subscriber': subscriber, 'confirm_url': confirm_url},
        to=[subscriber.email],
    )


def send_newsletter_issue(subscriber, issue) -> bool:
    """Send a newsletter issue to a single subscriber.

    Used by the dashboard's "Send issue" button. The unsubscribe link is
    always rendered so every email is CAN-SPAM friendly.
    """
    issue_url = (
        f'{site_base_url()}'
        f'{reverse("blog:newsletter_issue", args=[issue.number])}'
    )
    unsubscribe_url = (
        f'{site_base_url()}'
        f'{reverse("blog:unsubscribe", args=[subscriber.unsubscribe_token])}'
    )
    return send_site_email(
        subject=f'Issue #{issue.number}: {issue.title_en}',
        template='email/newsletter_issue.html',
        context={
            'issue': issue,
            'issue_url': issue_url,
            'unsubscribe_url': unsubscribe_url,
            'subscriber': subscriber,
        },
        to=[subscriber.email],
    )


def new_subscriber_tokens() -> tuple[str, str]:
    """Generate fresh ``(confirm_token, unsubscribe_token)`` pair.

    Both tokens are URL-safe, 256 bits of entropy each, generated with
    ``secrets`` (not ``random``) to be unguessable.
    """
    return secrets.token_urlsafe(32), secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------


def safe_redirect(
    request,
    default: str = '/',
    allow_referer: bool = True,
) -> HttpResponseRedirect:
    """Return a redirect that cannot be hijacked into off-site URLs.

    Many of our public views accept a ``next`` parameter or fall back to
    ``HTTP_REFERER`` so that submitting a form returns the user to the
    page they came from.  Without validation that's a textbook open
    redirect — an attacker emails ``…/subscribe/?next=https://evil.com``
    and the server happily sends users there.

    This helper accepts a candidate redirect target only when:

    * It is a *relative* URL (always safe), **or**
    * Its host matches an entry in ``ALLOWED_HOSTS``.

    Anything else falls back to ``default``.
    """
    candidates: list[str] = []

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        candidates.append(next_url)
    if allow_referer:
        candidates.append(request.META.get('HTTP_REFERER', ''))

    allowed_hosts = set(settings.ALLOWED_HOSTS) | {request.get_host()}
    # ``ALLOWED_HOSTS = ['*']`` (DEBUG) means "accept any host" — but for
    # redirect validation we want stricter behaviour, so we drop the
    # wildcard and only trust the current request's host.
    if '*' in allowed_hosts:
        allowed_hosts = {request.get_host()}

    for raw in candidates:
        if not raw:
            continue
        parsed = urlparse(raw)
        # Relative URL: always safe to redirect to.
        if not parsed.netloc:
            if parsed.path.startswith('/'):
                qs = f'?{parsed.query}' if parsed.query else ''
                return HttpResponseRedirect(parsed.path + qs)
            continue
        # Absolute URL: only allow when host is one of ours.
        if parsed.netloc in allowed_hosts and parsed.scheme in ('http', 'https'):
            return HttpResponseRedirect(parsed.geturl())

    return HttpResponseRedirect(default)


def client_ip(request) -> str:
    """Best-effort client IP: honours ``X-Forwarded-For`` set by Nginx."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        # The leftmost address is the original client; everything after is
        # a chain of trusted proxies.
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def rate_limit(name: str, limit: int, window: int = 60):
    """Decorator: limit a view to ``limit`` calls per IP per ``window`` seconds.

    Backed by Django's cache framework, so it works with both the in-memory
    cache (development) and a shared store like Redis (production).

    When the limit is exceeded:

    * AJAX requests get a JSON response with HTTP 429.
    * Browser requests are redirected (via :func:`safe_redirect`) to the
      previous page so users see *something* rather than a blank 429.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # ``limit <= 0`` disables the limiter entirely (useful for tests).
            if limit <= 0:
                return view_func(request, *args, **kwargs)

            key = f'rl:{name}:{client_ip(request)}'
            current = cache.get(key, 0)
            if current >= limit:
                logger.warning('Rate limit hit on %s for %s', name, client_ip(request))
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'ok': False, 'message': 'Too many requests. Try again later.'},
                        status=429,
                    )
                return safe_redirect(request, default='/')

            # ``add`` is idempotent: only sets the key when it doesn't exist.
            # The ``incr`` then bumps the counter atomically. Together they
            # initialise the counter exactly once per window.
            try:
                cache.add(key, 0, window)
                cache.incr(key)
            except ValueError:
                # ``incr`` raises if the key disappeared between ``add`` and
                # ``incr`` — restart the counter for the remaining window.
                cache.set(key, 1, window)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def is_honeypot_filled(request, field: str = 'website') -> bool:
    """Return ``True`` if the hidden honeypot field was populated by a bot."""
    return bool((request.POST.get(field) or '').strip())
