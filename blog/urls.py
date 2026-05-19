"""Public URL configuration for the blog app.

URL philosophy:

* **Pretty, predictable paths.** ``/post/<slug>/``, ``/tag/<slug>/``,
  ``/products/<slug>/``. No query strings for primary navigation.
* **Stable entry points** for crawlers and aggregators: ``/feed.xml``,
  ``/sitemap.xml``, ``/robots.txt``, ``/healthz``.
* The ``app_name = 'blog'`` namespace lets us reverse URLs as
  ``{% url 'blog:post_detail' slug=… %}`` without ambiguity.
"""

from django.urls import path

from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    # ---- Reading surfaces ------------------------------------------------
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('tag/<slug:tag_slug>/', views.tag_list, name='tag_list'),
    path('search/', views.search, name='search'),
    path('now/', views.now_page, name='now'),

    # ---- Editorial pages -------------------------------------------------
    path('projects/', views.projects, name='projects'),
    path('uses/', views.uses, name='uses'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),

    # ---- Newsletter ------------------------------------------------------
    path('newsletter/', views.newsletter, name='newsletter'),
    path('newsletter/issue/<int:number>/', views.newsletter_issue, name='newsletter_issue'),
    path('newsletter/confirm/<str:token>/', views.confirm_subscription, name='confirm_subscription'),
    path('newsletter/unsubscribe/<str:token>/', views.unsubscribe, name='unsubscribe'),

    # ---- Static-ish pages ------------------------------------------------
    path('hire-me/', views.hire_me, name='hire_me'),
    path('about/', views.about, name='about'),

    # ---- Form endpoints (POST) ------------------------------------------
    path('subscribe/', views.subscribe, name='subscribe'),
    path('contact/', views.contact, name='contact'),

    # ---- Crawler / monitor entry points ----------------------------------
    path('feed.xml', LatestPostsFeed(), name='rss'),
    path('robots.txt', views.robots_txt, name='robots'),
    path('healthz', views.healthz, name='healthz'),
]
