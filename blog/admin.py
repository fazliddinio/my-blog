from django.contrib import admin
from .models import (
    Post, Project, UsesCategory, UsesItem, Product, ProductBullet,
    NewsletterSubscriber, NewsletterIssue, ContactMessage, TimelineEntry,
)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'date', 'tag', 'read_time', 'featured']
    list_filter = ['featured', 'tag', 'date']
    search_fields = ['title_en', 'title_uz', 'dek_en']
    prepopulated_fields = {'slug': ('title_en',)}
    list_editable = ['featured']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'stars', 'order']
    list_editable = ['order', 'stars']


class UsesItemInline(admin.TabularInline):
    model = UsesItem
    extra = 1


@admin.register(UsesCategory)
class UsesCategoryAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'order']
    list_editable = ['order']
    inlines = [UsesItemInline]


class ProductBulletInline(admin.TabularInline):
    model = ProductBullet
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'kind_en', 'price_en', 'order']
    list_editable = ['order']
    inlines = [ProductBulletInline]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active']
    search_fields = ['email']


@admin.register(NewsletterIssue)
class NewsletterIssueAdmin(admin.ModelAdmin):
    list_display = ['number', 'date_en', 'title_en']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at', 'is_read']
    list_filter = ['is_read']
    list_editable = ['is_read']
    readonly_fields = ['email', 'message', 'created_at']


@admin.register(TimelineEntry)
class TimelineEntryAdmin(admin.ModelAdmin):
    list_display = ['period_en', 'description_en', 'order']
    list_editable = ['order']
