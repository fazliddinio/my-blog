"""Atom/RSS feed for the blog.

Exposed at ``/feed.xml`` (see ``blog/urls.py``). RSS readers and aggregators
discover the feed through the ``<link rel="alternate" …>`` tag in
``base.html``. The feed exposes the 20 most-recent published posts.
"""

from django.contrib.syndication.views import Feed
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed

from .models import Post
from .utils import render_content, site_base_url


class LatestPostsFeed(Feed):
    """Atom feed of the most recently published posts."""

    title = 'fazliddin.com'
    link = '/'
    description = 'Notes on building software, mostly.'

    # Atom is preferred over RSS 2.0: it has well-defined date semantics,
    # better escaping rules, and is what most modern readers expect.
    feed_type = Atom1Feed

    def items(self):
        # ``Post.published`` already filters out drafts/scheduled posts.
        return Post.published.all()[:20]

    def item_title(self, item: Post) -> str:
        return item.title_en

    def item_description(self, item: Post) -> str:
        # Render the body the same way the public site would so subscribers
        # see the post the way it appears in their browser.
        return render_content(item.content_en, item.content_format)

    def item_link(self, item: Post) -> str:
        # The site URL comes from ``SiteSettings`` so the feed always shows
        # absolute, canonical URLs even when crawled from a CDN/cache.
        return f'{site_base_url()}/post/{item.slug}/'

    def item_pubdate(self, item: Post):
        """Return a timezone-aware datetime for the item's publication date."""
        # ``Post.date`` is a ``DateField``; combine with midnight to satisfy
        # Atom's requirement for a full datetime, then make it timezone-aware.
        dt = timezone.datetime.combine(item.date, timezone.datetime.min.time())
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
