"""URL patterns for the editor-facing dashboard.

Every path here is gated by ``@login_required`` in the corresponding view.
The ``app_name`` namespace lets templates reverse URLs unambiguously, e.g.
``{% url 'dashboard:posts' %}``.
"""

from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    # ---- Auth ------------------------------------------------------------
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ---- Dashboard home --------------------------------------------------
    path('', views.index, name='index'),

    # ---- Posts -----------------------------------------------------------
    path('posts/', views.posts, name='posts'),
    path('posts/new/', views.post_create, name='post_create'),
    path('posts/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('posts/<int:pk>/delete/', views.post_delete, name='post_delete'),

    # ---- Projects --------------------------------------------------------
    path('projects/', views.projects, name='projects'),
    path('projects/new/', views.project_create, name='project_create'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),

    # ---- Products --------------------------------------------------------
    path('products/', views.products, name='products'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # ---- Newsletter ------------------------------------------------------
    path('newsletter/', views.newsletter, name='newsletter'),
    path('newsletter/issues/new/', views.issue_create, name='issue_create'),
    path('newsletter/issues/<int:pk>/edit/', views.issue_edit, name='issue_edit'),
    path('newsletter/issues/<int:pk>/delete/', views.issue_delete, name='issue_delete'),
    path('newsletter/issues/<int:pk>/send/', views.issue_send, name='issue_send'),
    path('newsletter/subscribers/<int:pk>/delete/', views.subscriber_delete, name='subscriber_delete'),
    path('newsletter/subscribers/<int:pk>/toggle/', views.subscriber_toggle, name='subscriber_toggle'),
    path('newsletter/subscribers.csv', views.subscribers_csv, name='subscribers_csv'),

    # ---- Contact messages -----------------------------------------------
    path('messages/', views.message_list, name='messages'),
    path('messages/<int:pk>/read/', views.message_read, name='message_read'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    # ---- /uses page ------------------------------------------------------
    path('uses/', views.uses, name='uses'),
    path('uses/categories/new/', views.uses_category_create, name='uses_category_create'),
    path('uses/categories/<int:pk>/edit/', views.uses_category_edit, name='uses_category_edit'),
    path('uses/categories/<int:pk>/delete/', views.uses_category_delete, name='uses_category_delete'),
    path('uses/items/new/', views.uses_item_create, name='uses_item_create'),
    path('uses/items/<int:pk>/edit/', views.uses_item_edit, name='uses_item_edit'),
    path('uses/items/<int:pk>/delete/', views.uses_item_delete, name='uses_item_delete'),

    # ---- Timeline (about page) ------------------------------------------
    path('timeline/', views.timeline, name='timeline'),
    path('timeline/new/', views.timeline_create, name='timeline_create'),
    path('timeline/<int:pk>/edit/', views.timeline_edit, name='timeline_edit'),
    path('timeline/<int:pk>/delete/', views.timeline_delete, name='timeline_delete'),

    # ---- Singletons & misc ----------------------------------------------
    path('settings/', views.site_settings_view, name='site_settings'),
    path('now/', views.now_edit, name='now_edit'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('testimonials/new/', views.testimonial_create, name='testimonial_create'),
    path('testimonials/<int:pk>/edit/', views.testimonial_edit, name='testimonial_edit'),
    path('testimonials/<int:pk>/delete/', views.testimonial_delete, name='testimonial_delete'),
]
