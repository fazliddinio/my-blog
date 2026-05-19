"""Blog domain models.

This module defines every persistent entity rendered on the public site:

* ``SiteSettings`` and ``NowPage`` are *singletons* (only ever a single row).
* ``Post`` is the heart of the blog and supports drafts, scheduling, series,
  bilingual content (EN/UZ), and Markdown or HTML bodies.
* ``Project`` / ``UsesCategory`` / ``UsesItem`` / ``Product`` / ``ProductBullet``
  power the static-but-editable section pages (Projects, Uses, Products).
* ``NewsletterSubscriber`` / ``NewsletterIssue`` back the newsletter flow
  (double opt-in, send tracking, secure tokens).
* ``ContactMessage`` and ``TimelineEntry`` are simple support models.

Every textual field has an ``_en`` / ``_uz`` pair so the same row can serve
both audiences without duplicating records.  Templates pick the right field
through the ``{% bi %}`` tag (see ``blog/templatetags/i18n_tags.py``).
"""

from __future__ import annotations

from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .managers import PublishedPostManager
from .utils import estimate_read_time, looks_like_markdown


# ---------------------------------------------------------------------------
# Singletons (settings + now page)
# ---------------------------------------------------------------------------

# Cache keys for the singletons. Versioned so we can bump them later without
# flushing the whole cache.
_SITE_SETTINGS_CACHE_KEY = 'site_settings:v1'
_NOW_PAGE_CACHE_KEY = 'now_page:v1'


class SiteSettings(models.Model):
    """Singleton holding site-wide tunables that admins should be able to change.

    The model is deliberately kept tiny — anything that *requires* a server
    restart belongs in ``config/settings.py``; everything that an editor might
    want to flip without redeploying lives here (analytics domain, Calendly
    URL, comments toggle, etc.).

    Use :meth:`cached` for read-heavy paths (templates, context processors)
    and :meth:`load` when you need to mutate the row.
    """

    site_url = models.URLField(default='https://fazliddin.com')
    analytics_domain = models.CharField(
        max_length=200, blank=True,
        help_text='Plausible domain, e.g. fazliddin.com',
    )
    giscus_repo = models.CharField(max_length=200, blank=True, help_text='user/repo')
    giscus_repo_id = models.CharField(max_length=100, blank=True)
    giscus_category_id = models.CharField(max_length=100, blank=True, default='General')
    calendly_url = models.URLField(blank=True)
    double_opt_in = models.BooleanField(default=True)
    comments_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Site settings'

    def __str__(self) -> str:
        return 'Site settings'

    def save(self, *args, **kwargs):
        # Invalidate the read cache so changes are visible immediately.
        super().save(*args, **kwargs)
        cache.delete(_SITE_SETTINGS_CACHE_KEY)

    @classmethod
    def load(cls) -> 'SiteSettings':
        """Return the row, creating it on first access (always pk=1)."""
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def cached(cls) -> 'SiteSettings':
        """Return a cached copy. Cheap to call from every view/template."""
        obj = cache.get(_SITE_SETTINGS_CACHE_KEY)
        if obj is None:
            obj = cls.load()
            # 5 minutes is plenty: changes are rare and `save()` busts the cache.
            cache.set(_SITE_SETTINGS_CACHE_KEY, obj, 300)
        return obj


class NowPage(models.Model):
    """Singleton powering the ``/now`` page (https://nownownow.com/about).

    A single, casually-updated paragraph about what the author is working on
    *right now*. Lighter touch than a blog post — we just store one body of
    text per language plus a content format.
    """

    content_en = models.TextField(blank=True, help_text='HTML or Markdown')
    content_uz = models.TextField(blank=True)
    content_format = models.CharField(
        max_length=10,
        choices=[('html', 'HTML'), ('markdown', 'Markdown')],
        default='markdown',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Now page'

    def __str__(self) -> str:
        return 'Now page'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(_NOW_PAGE_CACHE_KEY)

    @classmethod
    def load(cls) -> 'NowPage':
        """Return the row, creating it on first access (always pk=1)."""
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class Testimonial(models.Model):
    """A single quote shown on the Hire-me page. Ordering is editor-controlled."""

    name = models.CharField(max_length=100)
    role_en = models.CharField(max_length=200)
    role_uz = models.CharField(max_length=200, blank=True)
    quote_en = models.TextField()
    quote_uz = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------


class Post(models.Model):
    """Long-form essay: the primary content type of the site.

    Posts can be **drafts** or **published**, optionally **scheduled** via
    ``published_at``, and can belong to a **series**. The body is stored
    raw and rendered through :func:`blog.utils.render_content` at request
    time, so we can support both HTML and Markdown with the same model.

    Two managers are exposed:

    * ``Post.objects``   — every row, including drafts. Used by the dashboard.
    * ``Post.published`` — only public, time-eligible posts. Used by every
      public view; this is the default for the public site.

    The split is intentional: it makes "draft is publicly visible" bugs
    impossible at the queryset level — a public view literally cannot see
    drafts unless it explicitly opts into ``Post.objects``.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    class ContentFormat(models.TextChoices):
        HTML = 'html', 'HTML'
        MARKDOWN = 'markdown', 'Markdown'

    slug = models.SlugField(max_length=200, unique=True)
    date = models.DateField(db_index=True)

    # Bilingual fields. ``_en`` is required, ``_uz`` is optional (we fall back
    # to English when a translation hasn't been written yet).
    title_en = models.CharField(max_length=300)
    title_uz = models.CharField(max_length=300, blank=True)
    dek_en = models.TextField(help_text='Short description (English)')
    dek_uz = models.TextField(blank=True, help_text='Short description (Uzbek)')

    tag = models.CharField(max_length=50, db_index=True)
    read_time = models.PositiveIntegerField(
        default=1,
        help_text='Reading time (minutes); auto-calculated if left blank.',
    )
    featured = models.BooleanField(default=False, db_index=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PUBLISHED, db_index=True,
    )
    # ``published_at`` is set on first publish and is what the public manager
    # filters on. Setting it to a future date schedules the post.
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    series = models.CharField(max_length=100, blank=True, db_index=True)
    series_part = models.PositiveSmallIntegerField(null=True, blank=True)

    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True)

    content_format = models.CharField(
        max_length=10, choices=ContentFormat.choices, default=ContentFormat.MARKDOWN,
    )
    content_en = models.TextField(blank=True, help_text='Full body (English)')
    content_uz = models.TextField(blank=True, help_text='Full body (Uzbek)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedPostManager()

    class Meta:
        ordering = ['-date', '-published_at']
        # Most lookup paths filter by ``status`` then sort by ``-date``, or
        # surface featured posts first; the composite indexes match those.
        indexes = [
            models.Index(fields=['status', '-date']),
            models.Index(fields=['featured', '-date']),
        ]

    def __str__(self) -> str:
        return self.title_en

    def get_absolute_url(self) -> str:
        return reverse('blog:post_detail', args=[self.slug])

    @property
    def year(self) -> int:
        """Year shown on the listings — derived from ``date`` (not ``published_at``)."""
        return self.date.year

    @property
    def is_translation_complete(self) -> bool:
        """Used in the dashboard list to highlight posts missing Uzbek copy."""
        return bool(self.title_uz and self.dek_uz and self.content_uz)

    @property
    def tag_slug(self) -> str:
        return slugify(self.tag)

    def save(self, *args, **kwargs):
        # Auto-generate the slug on first save so editors don't have to think
        # about URL slugs unless they want a custom one.
        if not self.slug:
            self.slug = slugify(self.title_en)

        # ``read_time`` is editor-overridable. Only auto-calculate when the
        # editor left it blank/zero AND we actually have something to count.
        if (not self.read_time or self.read_time <= 0) and self.content_en:
            self.read_time = estimate_read_time(self.content_en)

        # First time a post moves to "published" we stamp ``published_at``.
        # An explicit value (e.g. for scheduling) is never overwritten.
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        # Safety net: if an editor wrote Markdown but forgot to set the
        # format dropdown, render correctly anyway.  ``looks_like_markdown``
        # is conservative — it only triggers when the body has no block-level
        # HTML tags AND has clear Markdown markers.
        if (
            self.content_format == self.ContentFormat.HTML
            and looks_like_markdown(self.content_en)
        ):
            self.content_format = self.ContentFormat.MARKDOWN

        super().save(*args, **kwargs)

    # -- Navigation helpers used on the post detail page -------------------

    def get_series_posts(self):
        """All published siblings in the same series, ordered by part then date."""
        if not self.series:
            return Post.published.none()
        return Post.published.filter(series=self.series).order_by('series_part', 'date')

    def get_prev_post(self):
        """Previous published post by date, or ``None`` for the first post."""
        return Post.published.filter(date__lt=self.date).order_by('-date').first()

    def get_next_post(self):
        """Next published post by date, or ``None`` for the latest post."""
        return Post.published.filter(date__gt=self.date).order_by('date').first()

    def get_related_posts(self, limit: int = 3):
        """Top ``limit`` posts that share the same tag (excluding ``self``)."""
        return Post.published.filter(tag=self.tag).exclude(pk=self.pk)[:limit]


# ---------------------------------------------------------------------------
# Projects, Uses, Products
# ---------------------------------------------------------------------------


class Project(models.Model):
    """A side-project entry shown on ``/projects``.

    Mirrors a typical "GitHub project" card: name, tagline, language, stars,
    and an optional link. ``order`` lets editors put their best work first.
    """

    name = models.CharField(max_length=100)
    tagline_en = models.CharField(max_length=300)
    tagline_uz = models.CharField(max_length=300, blank=True)
    desc_en = models.TextField()
    desc_uz = models.TextField(blank=True)
    stars = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=50)
    href = models.CharField(max_length=500, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return self.name

    @property
    def lang_color(self) -> str:
        """Return the GitHub-style colour swatch for this project's language."""
        # Mirrors the colours GitHub uses on repo cards. Falls back to a
        # neutral grey for languages we haven't enumerated.
        colors = {
            'TypeScript': '#3178c6', 'JavaScript': '#f7df1e',
            'Go': '#00add8', 'Python': '#3572a5', 'Rust': '#dea584',
            'Swift': '#f05138', 'Ruby': '#cc342d', 'Java': '#b07219',
        }
        return colors.get(self.language, '#888')


class UsesCategory(models.Model):
    """A heading on the ``/uses`` page (e.g. *Editor*, *Hardware*)."""

    title_en = models.CharField(max_length=100)
    title_uz = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Uses categories'

    def __str__(self) -> str:
        return self.title_en


class UsesItem(models.Model):
    """A single tool/device under a :class:`UsesCategory`."""

    category = models.ForeignKey(UsesCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    note_en = models.TextField(blank=True)
    note_uz = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """A thing-for-sale shown on ``/products`` (e.g. a course or eBook).

    The ``checkout_url`` field is the only required piece for monetisation:
    when set the front-end CTA links straight to it (Stripe, Gumroad, …);
    when empty we show a "coming soon" toast instead.
    """

    slug = models.SlugField(max_length=200, unique=True, blank=True)
    name_en = models.CharField(max_length=200)
    name_uz = models.CharField(max_length=200, blank=True)
    kind_en = models.CharField(max_length=50)
    kind_uz = models.CharField(max_length=50, blank=True)
    price_en = models.CharField(max_length=50)
    price_uz = models.CharField(max_length=50, blank=True)
    blurb_en = models.TextField()
    blurb_uz = models.TextField(blank=True)
    content_en = models.TextField(blank=True, help_text='Body (HTML or Markdown)')
    content_uz = models.TextField(blank=True, help_text='Body (HTML or Markdown)')
    cta_en = models.CharField(max_length=50)
    cta_uz = models.CharField(max_length=50, blank=True)
    checkout_url = models.URLField(blank=True, help_text='Stripe / Gumroad / payment link')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return self.name_en

    def get_absolute_url(self) -> str:
        return reverse('blog:product_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)


class ProductBullet(models.Model):
    """One bullet under a :class:`Product` ("Includes 4 hours of video", …)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bullets')
    text_en = models.CharField(max_length=200)
    text_uz = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return self.text_en


# ---------------------------------------------------------------------------
# Newsletter / Contact / Timeline
# ---------------------------------------------------------------------------


class NewsletterSubscriber(models.Model):
    """A newsletter subscriber.

    Two URL-safe random tokens are stored at signup so that confirmation and
    unsubscribe links are unguessable and don't expose the primary key. They
    are indexed because they are looked up on every confirm/unsubscribe hit.
    """

    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    confirmed = models.BooleanField(default=False)
    confirm_token = models.CharField(max_length=64, blank=True, db_index=True)
    unsubscribe_token = models.CharField(max_length=64, blank=True, db_index=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self) -> str:
        return self.email


class NewsletterIssue(models.Model):
    """A single issue of the newsletter.

    ``date_en`` / ``date_uz`` are stored as freeform strings (e.g.
    *"April 2026"* or *"2026 aprel"*) rather than ``DateField`` because the
    display label rarely matches the actual send date and editors want full
    control over wording.
    """

    number = models.PositiveIntegerField(unique=True)
    date_en = models.CharField(max_length=50, help_text='Display date, e.g. April 2026')
    date_uz = models.CharField(max_length=50, blank=True)
    title_en = models.CharField(max_length=300)
    title_uz = models.CharField(max_length=300, blank=True)
    content_en = models.TextField(blank=True, help_text='Issue body (HTML or Markdown)')
    content_uz = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-number']

    def __str__(self) -> str:
        return f'Issue #{self.number}'


class ContactMessage(models.Model):
    """A message submitted through the contact form.

    The submitter's IP is recorded so that abusive sources can be identified
    and rate-limited; this is not exposed publicly.
    """

    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.email} — {self.created_at:%Y-%m-%d}'


class TimelineEntry(models.Model):
    """An entry on the ``/about`` page timeline ("2017 — 2021 …")."""

    period_en = models.CharField(max_length=100)
    period_uz = models.CharField(max_length=100, blank=True)
    description_en = models.TextField()
    description_uz = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Timeline entries'

    def __str__(self) -> str:
        return self.period_en
