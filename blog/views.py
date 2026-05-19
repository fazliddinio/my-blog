"""Public-facing views for the blog.

Conventions used throughout this module:

* The :class:`~blog.managers.PublishedPostManager` (``Post.published``) is
  the **only** queryset entry point used here. Drafts cannot leak.
* AJAX submissions (``X-Requested-With: XMLHttpRequest``) get JSON; plain
  form submissions get HTML redirects via :func:`~blog.utils.safe_redirect`.
* Every form-handling view is rate-limited and honeypot-protected.
* Read-only pages set ``Cache-Control`` and vary on the language cookie so
  edge caches (CDN/Nginx) can serve repeat requests without hitting Django.
"""

from __future__ import annotations

import logging

from django.conf import settings as dj_settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.vary import vary_on_cookie

from .forms import ContactForm, NewsletterForm
from .models import (
    ContactMessage, NewsletterIssue, NewsletterSubscriber, NowPage,
    Post, Product, Project, SiteSettings, Testimonial, TimelineEntry,
    UsesCategory,
)
from .utils import (
    client_ip, is_honeypot_filled, new_subscriber_tokens, rate_limit,
    safe_redirect, send_contact_notification, send_subscriber_confirmation,
    site_base_url,
)

logger = logging.getLogger('blog')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _published_posts():
    """Return the canonical "everything the public can see" queryset."""
    return Post.published.all()


def _is_ajax(request) -> bool:
    """``True`` when the request was issued via ``fetch`` / ``XMLHttpRequest``."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _ajax_json(
    ok: bool,
    message: str = '',
    errors: dict | None = None,
    status: int = 200,
):
    """Build a consistent JSON envelope used by every AJAX form response."""
    payload: dict = {'ok': ok}
    if message:
        payload['message'] = message
    if errors:
        payload['errors'] = errors
    return JsonResponse(payload, status=status)


def _all_tags() -> list[str]:
    """Distinct list of tags used by published posts (sorted alphabetically)."""
    return list(_published_posts().order_by('tag').values_list('tag', flat=True).distinct())


# ---------------------------------------------------------------------------
# Public views
# ---------------------------------------------------------------------------


@vary_on_cookie
@cache_control(public=True, max_age=60)
def home(request):
    """Site homepage: commercial hero, offers, proof, products, writing, newsletter."""
    posts = list(_published_posts()[:30])

    featured = [p for p in posts if p.featured][:3]
    if not featured:
        featured = posts[:3]
        recent = posts[3:7]
    else:
        recent = [p for p in posts if not p.featured][:4]

    return render(request, 'home.html', {
        'featured': featured,
        'recent': recent,
        'products': list(Product.objects.prefetch_related('bullets').all()[:3]),
        'testimonials': list(Testimonial.objects.all()[:3]),
        'newsletter_form': NewsletterForm(),
    })


@vary_on_cookie
@cache_control(public=True, max_age=60)
def blog_list(request):
    """Paginated list of every published post, grouped by year."""
    posts_qs = _published_posts()
    tags = ['all'] + _all_tags()

    # 30 posts per page strikes a balance between SEO (one big page is
    # easier for crawlers) and load time on slow connections.
    paginator = Paginator(posts_qs, 30)
    try:
        page = paginator.page(request.GET.get('page', 1))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        # Out-of-range pages 404 rather than redirect: this surfaces broken
        # internal links instead of silently masking them.
        raise Http404('No more posts.')

    posts_by_year: dict[int, list] = {}
    for post in page.object_list:
        posts_by_year.setdefault(post.year, []).append(post)
    years_sorted = sorted(posts_by_year.items(), key=lambda x: x[0], reverse=True)

    return render(request, 'blog/list.html', {
        'posts_by_year': years_sorted,
        'tags': tags,
        'current_tag': 'all',
        'page_obj': page,
        'paginator': paginator,
    })


@vary_on_cookie
@cache_control(public=True, max_age=60)
def tag_list(request, tag_slug: str):
    """Posts tagged with the given slug.

    Tags themselves are stored as free-text on each ``Post`` row; we slugify
    them on the fly and resolve back to the canonical (display) tag here.
    """
    posts_qs = _published_posts()

    # Quick path: the slug already matches the stored value (common case).
    tag = (
        posts_qs
        .filter(Q(tag__iexact=tag_slug) | Q(tag__iexact=tag_slug.replace('-', ' ')))
        .values_list('tag', flat=True)
        .first()
    )

    # Fallback: scan distinct tags and slugify each until we find a match.
    # This handles unusual cases like ``"My Cool Tag"`` -> ``"my-cool-tag"``.
    if not tag:
        for candidate in _all_tags():
            if slugify(candidate) == tag_slug:
                tag = candidate
                break

    if not tag:
        raise Http404('Tag not found.')

    posts_qs = posts_qs.filter(tag=tag)
    paginator = Paginator(posts_qs, 30)
    try:
        page = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)

    posts_by_year: dict[int, list] = {}
    for post in page.object_list:
        posts_by_year.setdefault(post.year, []).append(post)
    years_sorted = sorted(posts_by_year.items(), key=lambda x: x[0], reverse=True)

    return render(request, 'blog/list.html', {
        'posts_by_year': years_sorted,
        'tags': ['all'] + _all_tags(),
        'current_tag': tag,
        'tag_slug': tag_slug,
        'page_obj': page,
        'paginator': paginator,
    })


@vary_on_cookie
@cache_control(public=True, max_age=60)
def post_detail(request, slug):
    """Render a single post plus its prev/next/related links and series nav."""
    # ``Post.published`` already filters out drafts; this lookup will 404
    # for any unpublished slug.
    post = get_object_or_404(Post.published, slug=slug)
    return render(request, 'blog/detail.html', {
        'post': post,
        'related_posts': list(post.get_related_posts()),
        'prev_post': post.get_prev_post(),
        'next_post': post.get_next_post(),
        'series_posts': list(post.get_series_posts()) if post.series else [],
    })


def search(request):
    """Full-text-ish search across post titles, descriptions, body, and tags.

    Uses Postgres ``ILIKE`` (``__icontains``); fast enough for the current
    corpus (tens to low-hundreds of posts). Migrate to ``SearchVector`` when
    the result count or post count starts to bite.
    """
    query = (request.GET.get('q') or '').strip()
    too_short = bool(query) and len(query) < 2
    results: list = []
    page = None
    paginator = None

    if query and not too_short:
        qs = _published_posts().filter(
            Q(title_en__icontains=query)
            | Q(title_uz__icontains=query)
            | Q(dek_en__icontains=query)
            | Q(dek_uz__icontains=query)
            | Q(content_en__icontains=query)
            | Q(content_uz__icontains=query)
            | Q(tag__icontains=query)
        )
        paginator = Paginator(qs, 25)
        try:
            page = paginator.page(request.GET.get('page', 1))
        except (PageNotAnInteger, EmptyPage):
            page = paginator.page(1)
        results = list(page.object_list)

    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'too_short': too_short,
        'page_obj': page,
        'paginator': paginator,
    })


def now_page(request):
    """The ``/now`` page (a casually-updated "what I'm doing right now")."""
    return render(request, 'now.html', {'now_page': NowPage.load()})


def projects(request):
    """List of side projects."""
    return render(request, 'projects.html', {'projects': Project.objects.all()})


def uses(request):
    """Stack page: tools, hardware, services."""
    # Prefetch items so each category renders without an extra query.
    categories = UsesCategory.objects.prefetch_related('items').all()
    return render(request, 'uses.html', {'categories': categories})


def products(request):
    """Public product listing."""
    return render(
        request,
        'products.html',
        {'products': Product.objects.prefetch_related('bullets').all()},
    )


def product_detail(request, slug):
    """Single product page with bullets and a checkout CTA."""
    product = get_object_or_404(Product.objects.prefetch_related('bullets'), slug=slug)
    return render(request, 'products/detail.html', {'product': product})


def newsletter(request):
    """Newsletter landing page: signup form + recent issues."""
    issues = NewsletterIssue.objects.all()[:8]
    return render(request, 'newsletter.html', {
        'issues': issues,
        'newsletter_form': NewsletterForm(),
    })


def newsletter_issue(request, number):
    """Individual newsletter issue (the same body that subscribers received)."""
    issue = get_object_or_404(NewsletterIssue, number=number)
    return render(request, 'newsletter/detail.html', {'issue': issue})


def hire_me(request):
    """Hire-me / consulting page with services, testimonials, contact form."""
    settings_obj = SiteSettings.cached()
    return render(request, 'hire_me.html', {
        'contact_form': ContactForm(),
        'testimonials': list(Testimonial.objects.all()),
        'calendly_url': settings_obj.calendly_url,
    })


def about(request):
    """About page (timeline + bio)."""
    return render(request, 'about.html', {'timeline': TimelineEntry.objects.all()})


@require_http_methods(['GET', 'HEAD'])
@cache_control(public=True, max_age=3600)
def robots_txt(request):
    """``/robots.txt``: tells crawlers where they can and cannot go."""
    body = '\n'.join([
        'User-agent: *',
        # Editorial surfaces — never index.
        'Disallow: /dashboard/',
        f'Disallow: /{dj_settings.ADMIN_URL}',
        'Allow: /',
        f'Sitemap: {site_base_url()}/sitemap.xml',
        '',  # trailing newline
    ])
    return HttpResponse(body, content_type='text/plain')


@require_http_methods(['GET', 'HEAD'])
def healthz(request):
    """Liveness endpoint for uptime monitors and load balancers.

    Intentionally tiny: returns ``200 OK`` with ``ok`` body when the WSGI
    process is up. Doesn't hit the database — keep it cheap.
    """
    return HttpResponse('ok', content_type='text/plain')


def custom_404(request, exception):
    """Branded 404 page (registered as ``handler404``)."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Branded 500 page (registered as ``handler500``)."""
    return render(request, '500.html', status=500)


# ---------------------------------------------------------------------------
# Newsletter & contact (public form endpoints)
# ---------------------------------------------------------------------------


@require_POST
@never_cache
@rate_limit('subscribe', limit=dj_settings.RATELIMIT_SUBSCRIBE)
def subscribe(request):
    """Newsletter signup endpoint.

    Implements double opt-in (when enabled in ``SiteSettings``):

    1. Submitter sends email -> we store the row, send confirmation email.
    2. Submitter clicks the confirm link -> :func:`confirm_subscription`
       flips ``confirmed=True`` and the row becomes mailable.

    Honeypot-filled requests are treated as success without persisting
    anything — that gives the bot no signal that its scrape was rejected.
    """
    # Bot? Pretend we accepted it. The bot moves on; the database stays clean.
    if is_honeypot_filled(request):
        if _is_ajax(request):
            return _ajax_json(True, 'Subscribed!')
        return safe_redirect(request, default='/')

    form = NewsletterForm(request.POST)
    settings_obj = SiteSettings.cached()
    if form.is_valid():
        email = form.cleaned_data['email'].lower()
        confirm_token, unsubscribe_token = new_subscriber_tokens()

        obj, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                'confirm_token': confirm_token,
                'unsubscribe_token': unsubscribe_token,
            },
        )

        # Existing subscriber re-signing up: re-activate them and backfill
        # any tokens that may be missing (legacy rows).
        if not created:
            obj.is_active = True
            if not obj.unsubscribe_token:
                obj.unsubscribe_token = unsubscribe_token
            if not obj.confirm_token:
                obj.confirm_token = confirm_token

        if settings_obj.double_opt_in and not obj.confirmed:
            obj.confirmed = False
            obj.save()
            send_subscriber_confirmation(obj)
            msg = 'Almost there — check your email to confirm.'
        else:
            obj.confirmed = True
            obj.confirmed_at = timezone.now()
            obj.save()
            msg = 'Subscribed — thanks!'

        if _is_ajax(request):
            return _ajax_json(True, msg)
        return safe_redirect(request, default='/')

    if _is_ajax(request):
        return _ajax_json(False, 'Please enter a valid email.', errors=form.errors, status=400)
    return safe_redirect(request, default='/')


@never_cache
def confirm_subscription(request, token):
    """Endpoint hit when the user clicks the confirmation email link."""
    sub = get_object_or_404(NewsletterSubscriber, confirm_token=token)
    sub.confirmed = True
    sub.confirmed_at = timezone.now()
    sub.is_active = True
    sub.save()
    return render(request, 'newsletter/confirmed.html', {'email': sub.email})


@never_cache
def unsubscribe(request, token):
    """One-click unsubscribe link rendered at the bottom of every email.

    Idempotent: deactivating an already-deactivated subscriber is fine.
    """
    sub = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
    sub.is_active = False
    sub.save()
    return render(request, 'newsletter/unsubscribed.html', {'email': sub.email})


@require_POST
@never_cache
@rate_limit('contact', limit=dj_settings.RATELIMIT_CONTACT)
def contact(request):
    """Contact-form endpoint. Same shape as :func:`subscribe`.

    Successful submissions trigger an email notification to the site
    owner (configured via ``DJANGO_CONTACT_NOTIFY_EMAIL``). Bots filling
    the honeypot get a silent fake-success response.
    """
    if is_honeypot_filled(request):
        if _is_ajax(request):
            return _ajax_json(True, 'Message sent!')
        return safe_redirect(request, default='/hire-me/')

    form = ContactForm(request.POST)
    if form.is_valid():
        message: ContactMessage = form.save(commit=False)
        # Recording the IP helps us identify and block abusive sources;
        # it is not displayed publicly.
        message.ip = client_ip(request)
        message.save()
        send_contact_notification(message)

        if _is_ajax(request):
            return _ajax_json(True, 'Message sent — talk soon!')
        return safe_redirect(request, default='/hire-me/')

    if _is_ajax(request):
        return _ajax_json(
            False,
            'Please check the fields and try again.',
            errors=form.errors,
            status=400,
        )
    return safe_redirect(request, default='/hire-me/')
