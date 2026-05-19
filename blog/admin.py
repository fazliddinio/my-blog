"""Django-admin registrations for the blog models.

The dashboard at ``/dashboard/`` is the *primary* editing surface; the
built-in admin is kept around for super-user maintenance (bulk fixes,
debugging, occasional one-off edits).
"""

from django.contrib import admin

from .models import (
    ContactMessage, NewsletterIssue, NewsletterSubscriber, NowPage,
    Post, Product, ProductBullet, Project, SiteSettings, Testimonial,
    TimelineEntry, UsesCategory, UsesItem,
)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin view tuned for the most common editor workflows."""

    list_display = ['title_en', 'status', 'date', 'tag', 'featured']
    list_filter = ['status', 'featured', 'tag']
    search_fields = ['title_en', 'title_uz', 'dek_en']
    # Auto-fill the slug from the English title — editors don't usually want
    # to think about URL slugs, and the model itself also generates one on
    # ``save()`` if this field is left blank.
    prepopulated_fields = {'slug': ('title_en',)}


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Subscriber list with confirmation/active flags surfaced for triage."""

    list_display = ['email', 'confirmed', 'is_active', 'subscribed_at']
    search_fields = ['email']


# Models below have simple admin needs — the default ModelAdmin is fine.
admin.site.register(Project)
admin.site.register(UsesCategory)
admin.site.register(UsesItem)
admin.site.register(Product)
admin.site.register(ProductBullet)
admin.site.register(NewsletterIssue)
admin.site.register(ContactMessage)
admin.site.register(TimelineEntry)
admin.site.register(SiteSettings)
admin.site.register(NowPage)
admin.site.register(Testimonial)
