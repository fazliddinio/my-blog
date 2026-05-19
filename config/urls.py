"""Root URL configuration.

This file wires together the three top-level surfaces of the project:

* ``/<ADMIN_URL>``          — Django's built-in admin (path is configurable
  via the ``DJANGO_ADMIN_URL`` env var so production can hide it behind a
  hard-to-guess slug).
* ``/dashboard/``           — the editor-facing CMS dashboard.
* ``/``                     — the public blog (handled by ``blog.urls``).

Sitemap discovery and custom 404/500 handlers are registered here so
they're guaranteed to be in scope regardless of which sub-app is active.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from blog.sitemaps import PostSitemap, ProductSitemap

# Sitemap registry. Add new section sitemaps here as the site grows.
sitemaps = {
    'posts': PostSitemap,
    'products': ProductSitemap,
}

urlpatterns = [
    # Admin path is configurable; default ``admin/`` is fine for dev.
    path(settings.ADMIN_URL, admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    # Blog must be last — its catch-all routes would shadow ``/dashboard/`` etc.
    path('', include('blog.urls')),
]

# Branded error pages.
handler404 = 'blog.views.custom_404'
handler500 = 'blog.views.custom_500'

# In DEBUG, Django serves user-uploaded media from /media/ for convenience.
# In production this is handled by Nginx (see DEPLOYMENT.md).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
