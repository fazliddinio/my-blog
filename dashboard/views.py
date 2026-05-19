"""Dashboard CRUD views — the editor-facing CMS.

Every view in this module is gated by ``@login_required``; this is the
admin surface for creating posts, sending newsletter issues, replying to
contact messages, etc.

Conventions used throughout:

* Read views (lists) accept a ``page`` query parameter and use
  :func:`_paginate` — keeps the dashboard fast even with thousands of rows.
* Mutating views are ``POST``-only and protected by Django's CSRF.
* The ``next`` redirect parameter is *always* run through
  :func:`url_has_allowed_host_and_scheme` to prevent open-redirect abuse.
* Logging captures auth events (login/logout, failed login) so we have a
  paper trail in gunicorn logs.
"""

from __future__ import annotations

import csv
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from blog.models import (
    ContactMessage, NewsletterIssue, NewsletterSubscriber, NowPage,
    Post, Product, ProductBullet, Project, SiteSettings, Testimonial,
    TimelineEntry, UsesCategory, UsesItem,
)
from blog.utils import client_ip, new_subscriber_tokens, rate_limit, send_newsletter_issue

from .forms import (
    NewsletterIssueForm, NowPageForm, PostForm, ProductForm,
    ProjectForm, SiteSettingsForm, TestimonialForm, TimelineEntryForm,
    UsesCategoryForm, UsesItemForm,
)

logger = logging.getLogger('dashboard')


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _safe_next(request, default: str = '') -> str:
    """Validate a ``next`` URL parameter against the allowed-hosts list.

    Returns ``default`` when the candidate is missing, malformed, or
    points off-site. This is what stops ``?next=https://evil.com`` from
    bouncing freshly-authenticated users to phishing pages.
    """
    candidate = request.POST.get('next') or request.GET.get('next') or ''
    allowed_hosts = set(settings.ALLOWED_HOSTS) | {request.get_host()}
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts=allowed_hosts,
        require_https=request.is_secure(),
    ):
        return candidate
    return default


@never_cache
@rate_limit('login', limit=settings.RATELIMIT_LOGIN, window=60)
def login_view(request):
    """Handle dashboard login (no third-party identity providers — username/password)."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            logger.info('Login: %s from %s', user.username, client_ip(request))
            return redirect(_safe_next(request, default=reverse('dashboard:index')))

        # Log failed attempts so brute-forcing leaves a trail.
        logger.warning(
            'Failed login attempt for "%s" from %s', username, client_ip(request),
        )
        messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/login.html', {
        'next': _safe_next(request, default=''),
    })


@require_POST
@login_required(login_url='/dashboard/login/')
def logout_view(request):
    """Log the current user out. POST-only to satisfy CSRF best practice."""
    logger.info('Logout: %s', request.user.username)
    logout(request)
    return redirect('blog:home')


# ---------------------------------------------------------------------------
# Dashboard home
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
@never_cache
def index(request):
    """Stats overview + recent activity (messages, subscribers)."""
    stats = {
        'posts': Post.objects.count(),
        'subscribers': NewsletterSubscriber.objects.filter(
            is_active=True, confirmed=True,
        ).count(),
        'pending_subs': NewsletterSubscriber.objects.filter(
            is_active=True, confirmed=False,
        ).count(),
        'messages': ContactMessage.objects.filter(is_read=False).count(),
        'projects': Project.objects.count(),
    }
    return render(request, 'dashboard/index.html', {
        'stats': stats,
        'recent_messages': ContactMessage.objects.all()[:5],
        'recent_subscribers': NewsletterSubscriber.objects.all()[:5],
    })


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------


def _paginate(request, qs, per_page: int = 25):
    """Pagination wrapper used by every list view in the dashboard.

    Tolerates bad ``page`` parameters (non-integer or out of range) by
    falling back to a sensible page rather than 404 — editors never want
    to be locked out of their own list view.
    """
    paginator = Paginator(qs, per_page)
    try:
        page = paginator.page(request.GET.get('page', 1))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages or 1)
    return page, paginator


# ---------------------------------------------------------------------------
# Posts CRUD
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def posts(request):
    """Paginated list of every post (drafts included)."""
    page, paginator = _paginate(request, Post.objects.all(), 25)
    return render(request, 'dashboard/posts.html', {
        'posts': page.object_list,
        'page_obj': page,
        'paginator': paginator,
    })


@login_required(login_url='/dashboard/login/')
def post_create(request):
    """Create a new post; ``request.FILES`` is required for the featured image."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post created.')
            return redirect('dashboard:posts')
    else:
        form = PostForm()
    return render(request, 'dashboard/post_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def post_edit(request, pk):
    """Edit an existing post. Same form as create; ``editing=True`` flips the UI."""
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated.')
            return redirect('dashboard:posts')
    else:
        form = PostForm(instance=post)
    return render(request, 'dashboard/post_form.html', {
        'form': form, 'editing': True, 'post': post,
    })


@login_required(login_url='/dashboard/login/')
@require_POST
def post_delete(request, pk):
    """Delete a post. POST-only so accidental link previews can't trigger it."""
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('dashboard:posts')


# ---------------------------------------------------------------------------
# Projects CRUD
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def projects(request):
    """List all projects."""
    return render(request, 'dashboard/projects.html', {'projects': Project.objects.all()})


@login_required(login_url='/dashboard/login/')
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project created.')
            return redirect('dashboard:projects')
    else:
        form = ProjectForm()
    return render(request, 'dashboard/project_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def project_edit(request, pk):
    obj = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated.')
            return redirect('dashboard:projects')
    else:
        form = ProjectForm(instance=obj)
    return render(request, 'dashboard/project_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def project_delete(request, pk):
    get_object_or_404(Project, pk=pk).delete()
    messages.success(request, 'Project deleted.')
    return redirect('dashboard:projects')


# ---------------------------------------------------------------------------
# Products CRUD
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def products(request):
    """List all products with their bullets prefetched (one query, not N+1)."""
    return render(request, 'dashboard/products.html', {
        'products': Product.objects.prefetch_related('bullets').all(),
    })


@login_required(login_url='/dashboard/login/')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            _save_bullets(request, product)
            messages.success(request, 'Product created.')
            return redirect('dashboard:products')
    else:
        form = ProductForm()
    return render(request, 'dashboard/product_form.html', {
        'form': form, 'editing': False, 'bullets': [],
    })


@login_required(login_url='/dashboard/login/')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            _save_bullets(request, product)
            messages.success(request, 'Product updated.')
            return redirect('dashboard:products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/product_form.html', {
        'form': form, 'editing': True, 'bullets': product.bullets.all(),
    })


def _save_bullets(request, product) -> None:
    """Persist bullet rows submitted alongside the product form.

    Bullets are entered in a dynamic ``en/uz`` row pair (see the dashboard
    template). We replace them wholesale on each save — the form is small
    enough that delete-and-recreate is simpler than diffing.
    """
    texts_en = request.POST.getlist('bullet_text_en')
    texts_uz = request.POST.getlist('bullet_text_uz')
    product.bullets.all().delete()
    for index, (en_text, uz_text) in enumerate(zip(texts_en, texts_uz)):
        if en_text.strip():
            ProductBullet.objects.create(
                product=product,
                text_en=en_text.strip(),
                text_uz=uz_text.strip(),
                order=index,
            )


@login_required(login_url='/dashboard/login/')
@require_POST
def product_delete(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, 'Product deleted.')
    return redirect('dashboard:products')


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def newsletter(request):
    """Combined view: issues list + paginated subscriber table."""
    sub_page, sub_paginator = _paginate(request, NewsletterSubscriber.objects.all(), 50)
    return render(request, 'dashboard/newsletter.html', {
        'issues': NewsletterIssue.objects.all(),
        'subscribers': sub_page.object_list,
        'sub_page': sub_page,
        'sub_paginator': sub_paginator,
        'total_subscribers': NewsletterSubscriber.objects.count(),
        'confirmed_count': NewsletterSubscriber.objects.filter(
            confirmed=True, is_active=True,
        ).count(),
    })


@login_required(login_url='/dashboard/login/')
def issue_create(request):
    if request.method == 'POST':
        form = NewsletterIssueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue created.')
            return redirect('dashboard:newsletter')
    else:
        form = NewsletterIssueForm()
    return render(request, 'dashboard/issue_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def issue_edit(request, pk):
    obj = get_object_or_404(NewsletterIssue, pk=pk)
    if request.method == 'POST':
        form = NewsletterIssueForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue updated.')
            return redirect('dashboard:newsletter')
    else:
        form = NewsletterIssueForm(instance=obj)
    return render(request, 'dashboard/issue_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def issue_delete(request, pk):
    get_object_or_404(NewsletterIssue, pk=pk).delete()
    messages.success(request, 'Issue deleted.')
    return redirect('dashboard:newsletter')


@login_required(login_url='/dashboard/login/')
@require_POST
def issue_send(request, pk):
    """Synchronously email an issue to every confirmed, active subscriber.

    Synchronous send is fine for the current subscriber count. Once we
    cross ~1k subscribers this should be moved into a background job
    (Celery / Django-Q) so the dashboard request doesn't block.
    """
    issue = get_object_or_404(NewsletterIssue, pk=pk)
    recipients = NewsletterSubscriber.objects.filter(is_active=True, confirmed=True)

    sent = 0
    failed = 0
    for sub in recipients:
        # Backfill tokens for legacy subscribers signed up before tokens existed.
        if not sub.unsubscribe_token:
            sub.confirm_token, sub.unsubscribe_token = new_subscriber_tokens()
            sub.save(update_fields=['confirm_token', 'unsubscribe_token'])
        if send_newsletter_issue(sub, issue):
            sent += 1
        else:
            failed += 1

    issue.sent_at = timezone.now()
    issue.save(update_fields=['sent_at'])

    if failed:
        messages.warning(
            request,
            f'Sent issue #{issue.number} to {sent} subscriber(s); {failed} failed.',
        )
    else:
        messages.success(request, f'Sent issue #{issue.number} to {sent} subscriber(s).')
    return redirect('dashboard:newsletter')


@login_required(login_url='/dashboard/login/')
@require_POST
def subscriber_delete(request, pk):
    """Hard-delete a subscriber. (Toggle to ``is_active=False`` for soft-delete.)"""
    get_object_or_404(NewsletterSubscriber, pk=pk).delete()
    messages.success(request, 'Subscriber removed.')
    return redirect('dashboard:newsletter')


@login_required(login_url='/dashboard/login/')
@require_POST
def subscriber_toggle(request, pk):
    """Flip ``is_active`` for a subscriber (soft-delete / restore)."""
    sub = get_object_or_404(NewsletterSubscriber, pk=pk)
    sub.is_active = not sub.is_active
    sub.save(update_fields=['is_active'])
    messages.success(
        request,
        f'Subscriber {"activated" if sub.is_active else "deactivated"}.',
    )
    return redirect('dashboard:newsletter')


@login_required(login_url='/dashboard/login/')
def subscribers_csv(request):
    """Export all subscribers as a CSV (for backups or migrating providers)."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
    writer = csv.writer(response)
    writer.writerow(['email', 'subscribed_at', 'confirmed', 'is_active'])
    for sub in NewsletterSubscriber.objects.all():
        writer.writerow([
            sub.email,
            sub.subscribed_at.isoformat(),
            'yes' if sub.confirmed else 'no',
            'yes' if sub.is_active else 'no',
        ])
    return response


# ---------------------------------------------------------------------------
# Contact messages
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def message_list(request):
    page, paginator = _paginate(request, ContactMessage.objects.all(), 25)
    return render(request, 'dashboard/messages.html', {
        'messages_list': page.object_list,
        'unread_count': ContactMessage.objects.filter(is_read=False).count(),
        'page_obj': page,
        'paginator': paginator,
    })


@login_required(login_url='/dashboard/login/')
@require_POST
def message_read(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = True
    msg.save(update_fields=['is_read'])
    messages.success(request, 'Marked as read.')
    return redirect('dashboard:messages')


@login_required(login_url='/dashboard/login/')
@require_POST
def message_delete(request, pk):
    get_object_or_404(ContactMessage, pk=pk).delete()
    messages.success(request, 'Message deleted.')
    return redirect('dashboard:messages')


# ---------------------------------------------------------------------------
# Uses / Stack
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def uses(request):
    return render(request, 'dashboard/uses.html', {
        'categories': UsesCategory.objects.prefetch_related('items').all(),
    })


@login_required(login_url='/dashboard/login/')
def uses_category_create(request):
    if request.method == 'POST':
        form = UsesCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('dashboard:uses')
    else:
        form = UsesCategoryForm()
    return render(request, 'dashboard/uses_category_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def uses_category_edit(request, pk):
    obj = get_object_or_404(UsesCategory, pk=pk)
    if request.method == 'POST':
        form = UsesCategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('dashboard:uses')
    else:
        form = UsesCategoryForm(instance=obj)
    return render(request, 'dashboard/uses_category_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def uses_category_delete(request, pk):
    get_object_or_404(UsesCategory, pk=pk).delete()
    messages.success(request, 'Category deleted.')
    return redirect('dashboard:uses')


@login_required(login_url='/dashboard/login/')
def uses_item_create(request):
    if request.method == 'POST':
        form = UsesItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item created.')
            return redirect('dashboard:uses')
    else:
        form = UsesItemForm()
    return render(request, 'dashboard/uses_item_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def uses_item_edit(request, pk):
    obj = get_object_or_404(UsesItem, pk=pk)
    if request.method == 'POST':
        form = UsesItemForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated.')
            return redirect('dashboard:uses')
    else:
        form = UsesItemForm(instance=obj)
    return render(request, 'dashboard/uses_item_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def uses_item_delete(request, pk):
    get_object_or_404(UsesItem, pk=pk).delete()
    messages.success(request, 'Item deleted.')
    return redirect('dashboard:uses')


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def timeline(request):
    return render(request, 'dashboard/timeline.html', {
        'entries': TimelineEntry.objects.all(),
    })


@login_required(login_url='/dashboard/login/')
def timeline_create(request):
    if request.method == 'POST':
        form = TimelineEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entry created.')
            return redirect('dashboard:timeline')
    else:
        form = TimelineEntryForm()
    return render(request, 'dashboard/timeline_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def timeline_edit(request, pk):
    obj = get_object_or_404(TimelineEntry, pk=pk)
    if request.method == 'POST':
        form = TimelineEntryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entry updated.')
            return redirect('dashboard:timeline')
    else:
        form = TimelineEntryForm(instance=obj)
    return render(request, 'dashboard/timeline_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def timeline_delete(request, pk):
    get_object_or_404(TimelineEntry, pk=pk).delete()
    messages.success(request, 'Entry deleted.')
    return redirect('dashboard:timeline')


# ---------------------------------------------------------------------------
# Site settings, Now page, testimonials
# ---------------------------------------------------------------------------


@login_required(login_url='/dashboard/login/')
def site_settings_view(request):
    """Edit the singleton :class:`~blog.models.SiteSettings` row."""
    settings_obj = SiteSettings.load()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings saved.')
            return redirect('dashboard:site_settings')
    else:
        form = SiteSettingsForm(instance=settings_obj)
    return render(request, 'dashboard/site_settings.html', {'form': form})


@login_required(login_url='/dashboard/login/')
def now_edit(request):
    """Edit the singleton :class:`~blog.models.NowPage` row."""
    page = NowPage.load()
    if request.method == 'POST':
        form = NowPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, 'Now page updated.')
            return redirect('dashboard:now_edit')
    else:
        form = NowPageForm(instance=page)
    return render(request, 'dashboard/now_form.html', {'form': form})


@login_required(login_url='/dashboard/login/')
def testimonials(request):
    return render(request, 'dashboard/testimonials.html', {
        'testimonials': Testimonial.objects.all(),
    })


@login_required(login_url='/dashboard/login/')
def testimonial_create(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Testimonial created.')
            return redirect('dashboard:testimonials')
    else:
        form = TestimonialForm()
    return render(request, 'dashboard/testimonial_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def testimonial_edit(request, pk):
    obj = get_object_or_404(Testimonial, pk=pk)
    if request.method == 'POST':
        form = TestimonialForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Testimonial updated.')
            return redirect('dashboard:testimonials')
    else:
        form = TestimonialForm(instance=obj)
    return render(request, 'dashboard/testimonial_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def testimonial_delete(request, pk):
    get_object_or_404(Testimonial, pk=pk).delete()
    messages.success(request, 'Testimonial deleted.')
    return redirect('dashboard:testimonials')
