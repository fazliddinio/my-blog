from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.home, name='home'),
    path('blog/', views.blog_list, name='blog_list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('projects/', views.projects, name='projects'),
    path('uses/', views.uses, name='uses'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('newsletter/', views.newsletter, name='newsletter'),
    path('newsletter/issue/<int:number>/', views.newsletter_issue, name='newsletter_issue'),
    path('hire-me/', views.hire_me, name='hire_me'),
    path('about/', views.about, name='about'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('contact/', views.contact, name='contact'),
]
