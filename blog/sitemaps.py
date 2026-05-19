"""XML sitemap generation.

Mounted at ``/sitemap.xml`` via ``config/urls.py`` so search engines can
discover every public URL. Crawlers are pointed here from ``robots.txt``.
"""

from django.contrib.sitemaps import Sitemap

from .models import Post, Product


class PostSitemap(Sitemap):
    """Sitemap entries for every published post."""

    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        # ``Post.published`` is already filtered; drafts never appear here.
        return Post.published.all()

    def lastmod(self, obj: Post):
        # Crawlers use ``lastmod`` to decide whether to re-fetch. ``updated_at``
        # changes whenever a post is edited, which is exactly what we want.
        return obj.updated_at


class ProductSitemap(Sitemap):
    """Sitemap entries for every product (course/book/SaaS)."""

    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Product.objects.all()

    def location(self, obj: Product) -> str:
        return f'/products/{obj.slug}/'
