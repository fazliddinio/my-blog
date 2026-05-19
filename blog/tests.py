"""Smoke tests for the public blog and key business rules.

Three test classes, grouped by concern:

* :class:`PublicPagesTest`  — homepage, list, detail, RSS, sitemap, search,
  404 page, and the all-important "drafts must not leak" guarantee.
* :class:`FormFlowTest`     — newsletter signup (incl. honeypot rejection),
  contact form validation, open-redirect protection.
* :class:`DashboardAuthTest`— login-required guard and POST-only logout.

Run locally with::

    python manage.py test blog

Tests rely on an in-memory cache via ``override_settings`` so the rate-limit
decorator's bookkeeping doesn't leak between cases.
"""

from __future__ import annotations

from datetime import date

from django.test import TestCase, override_settings
from django.urls import reverse

from blog.forms import ContactForm
from blog.models import NewsletterSubscriber, Post, SiteSettings


# Shared override: skip HTTPS redirect, run with DEBUG behaviour, and use
# a clean per-test in-memory cache so rate-limit counters don't bleed.
COMMON_OVERRIDES = dict(
    SECURE_SSL_REDIRECT=False,
    DJANGO_DEBUG=True,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
)


@override_settings(**COMMON_OVERRIDES)
class PublicPagesTest(TestCase):
    """Sanity-check every public reading surface and the draft hiding rule."""

    @classmethod
    def setUpTestData(cls):
        # A normal published post that should appear on every list.
        cls.post = Post.objects.create(
            slug='hello-world',
            date=date(2026, 1, 1),
            title_en='Hello World',
            dek_en='A first post.',
            tag='intro',
            read_time=2,
            status=Post.Status.PUBLISHED,
            content_en='<h2>Hello</h2><p>World</p>',
            featured=True,
        )
        # A draft that *must not* leak into any public response.
        cls.draft = Post.objects.create(
            slug='draft-post',
            date=date(2026, 2, 1),
            title_en='Hidden Draft',
            dek_en='Should not appear.',
            tag='intro',
            read_time=1,
            status=Post.Status.DRAFT,
            content_en='secret',
        )
        # Trigger the singleton creation so context processors don't 500.
        SiteSettings.load()

    # ---- Listings -------------------------------------------------------

    def test_home(self):
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello World')
        # Drafts must not appear in any listing.
        self.assertNotContains(response, 'Hidden Draft')

    def test_blog_list(self):
        response = self.client.get(reverse('blog:blog_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello World')
        self.assertNotContains(response, 'Hidden Draft')

    def test_tag_list(self):
        response = self.client.get(reverse('blog:tag_list', args=['intro']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello World')

    # ---- Detail / draft hiding -----------------------------------------

    def test_post_detail_published(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello World')

    def test_post_detail_draft_hidden(self):
        # Draft slugs must 404 — defence in depth via ``Post.published``.
        response = self.client.get(reverse('blog:post_detail', args=[self.draft.slug]))
        self.assertEqual(response.status_code, 404)

    # ---- Crawler-facing endpoints --------------------------------------

    def test_404(self):
        response = self.client.get('/this-should-not-exist/')
        self.assertEqual(response.status_code, 404)

    def test_robots_and_sitemap(self):
        robots = self.client.get(reverse('blog:robots'))
        self.assertEqual(robots.status_code, 200)
        # Crawlers should be blocked from editorial paths.
        self.assertIn(b'Disallow: /dashboard/', robots.content)

        sitemap = self.client.get('/sitemap.xml')
        self.assertEqual(sitemap.status_code, 200)

    def test_rss(self):
        response = self.client.get(reverse('blog:rss'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello World', response.content)

    # ---- Search --------------------------------------------------------

    def test_search(self):
        # Real query returns the matching post.
        hit = self.client.get(reverse('blog:search'), {'q': 'hello'})
        self.assertEqual(hit.status_code, 200)
        self.assertContains(hit, 'Hello World')

        # Single-character queries are rejected with a helpful hint.
        too_short = self.client.get(reverse('blog:search'), {'q': 'h'})
        self.assertContains(too_short, 'at least')

    def test_search_xss_safe(self):
        """User-supplied search terms must never be echoed as raw HTML."""
        response = self.client.get(
            reverse('blog:search'),
            {'q': '<script>alert(1)</script>'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<script>alert(1)</script>', response.content)


@override_settings(
    **COMMON_OVERRIDES,
    # Disable rate limiting for these tests; we're exercising form logic,
    # not throttling behaviour.
    RATELIMIT_SUBSCRIBE=100,
    RATELIMIT_CONTACT=100,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class FormFlowTest(TestCase):
    """Newsletter / contact / open-redirect protection."""

    def test_subscribe_creates_subscriber(self):
        response = self.client.post(reverse('blog:subscribe'), {
            'email': 'alice@example.com',
            'website': '',  # honeypot empty — legitimate user
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            NewsletterSubscriber.objects.filter(email='alice@example.com').exists()
        )

    def test_subscribe_honeypot_blocks(self):
        """Bots that fill the hidden ``website`` field must be silently dropped."""
        response = self.client.post(reverse('blog:subscribe'), {
            'email': 'bot@example.com',
            'website': 'http://spam.com',  # bot fingerprint
        }, follow=False)
        self.assertEqual(response.status_code, 302)
        # No row should have been created.
        self.assertFalse(
            NewsletterSubscriber.objects.filter(email='bot@example.com').exists()
        )

    def test_contact_validation(self):
        # Below the minimum length: rejected.
        too_short = ContactForm(data={
            'email': 'a@b.com', 'message': 'short', 'website': '',
        })
        self.assertFalse(too_short.is_valid())

        # Reasonable message: accepted.
        valid = ContactForm(data={
            'email': 'a@b.com',
            'message': 'A reasonably long message goes here.',
            'website': '',
        })
        self.assertTrue(valid.is_valid(), valid.errors)

    def test_open_redirect_blocked(self):
        """``?next=https://evil.com`` must not bounce users off-site."""
        response = self.client.post(
            reverse('blog:subscribe'),
            {
                'email': 'safe@example.com',
                'website': '',
                'next': 'https://evil.example.com/x',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.example.com', response['Location'])


@override_settings(SECURE_SSL_REDIRECT=False, DJANGO_DEBUG=True)
class DashboardAuthTest(TestCase):
    """Editor surfaces must be gated; logout must be POST-only."""

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/login/', response['Location'])

    def test_logout_requires_post(self):
        # GET to a POST-only endpoint should be rejected by Django's
        # ``@require_POST`` decorator with HTTP 405.
        response = self.client.get(reverse('dashboard:logout'))
        self.assertEqual(response.status_code, 405)
