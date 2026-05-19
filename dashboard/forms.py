"""Dashboard forms.

These are thin wrappers around the underlying models that add CSS classes
and placeholder text for the styled dashboard inputs. None of them carry
business logic of their own — that lives on the models.
"""

from django import forms

from blog.models import (
    NewsletterIssue, NowPage, Post, Product, ProductBullet, Project,
    SiteSettings, Testimonial, TimelineEntry, UsesCategory, UsesItem,
)


# Common dashboard widget attribute classes — kept as constants so a future
# CSS rename only has to happen in one place.
_INPUT = 'dash-form__input'
_TEXTAREA = 'dash-form__textarea'
_TEXTAREA_TALL = 'dash-form__textarea dash-form__textarea--tall'
_SELECT = 'dash-form__select'
_CHECKBOX = 'dash-form__checkbox'


class PostForm(forms.ModelForm):
    """Edit form for a :class:`~blog.models.Post`.

    Note that ``read_time`` is *not* required here — the model auto-fills
    it from the body's word count when the editor leaves it blank.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Match the model's behaviour: editor input is optional.
        self.fields['read_time'].required = False

    class Meta:
        model = Post
        fields = [
            'title_en', 'title_uz', 'slug', 'date', 'tag', 'read_time',
            'dek_en', 'dek_uz', 'content_en', 'content_uz', 'featured',
            'status', 'published_at', 'series', 'series_part',
            'featured_image', 'content_format',
        ]
        widgets = {
            'title_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Post title (English)'}),
            'title_uz': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Post title (Uzbek)'}),
            'slug': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'auto-generated-slug'}),
            'date': forms.DateInput(attrs={'class': _INPUT, 'type': 'date'}),
            'tag': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'e.g. caching, react, career'}),
            'read_time': forms.NumberInput(attrs={'class': _INPUT, 'placeholder': 'Auto on save'}),
            'dek_en': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3, 'placeholder': 'Short description (English)'}),
            'dek_uz': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3, 'placeholder': 'Short description (Uzbek)'}),
            'content_en': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 20, 'placeholder': 'HTML or Markdown'}),
            'content_uz': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 20, 'placeholder': 'Uzbek body (HTML or Markdown)'}),
            'featured': forms.CheckboxInput(attrs={'class': _CHECKBOX}),
            'status': forms.Select(attrs={'class': _SELECT}),
            'published_at': forms.DateTimeInput(attrs={'class': _INPUT, 'type': 'datetime-local'}),
            'series': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Optional series name'}),
            'series_part': forms.NumberInput(attrs={'class': _INPUT}),
            'featured_image': forms.FileInput(attrs={'class': _INPUT}),
            'content_format': forms.Select(attrs={'class': _SELECT}),
        }


class ProjectForm(forms.ModelForm):
    """Edit form for a :class:`~blog.models.Project`."""

    class Meta:
        model = Project
        fields = ['name', 'tagline_en', 'tagline_uz', 'desc_en', 'desc_uz',
                  'language', 'stars', 'href', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': _INPUT}),
            'tagline_en': forms.TextInput(attrs={'class': _INPUT}),
            'tagline_uz': forms.TextInput(attrs={'class': _INPUT}),
            'desc_en': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'desc_uz': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'language': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'TypeScript, Go, Python...'}),
            'stars': forms.NumberInput(attrs={'class': _INPUT}),
            'href': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'https://github.com/...'}),
            'order': forms.NumberInput(attrs={'class': _INPUT}),
        }


class ProductForm(forms.ModelForm):
    """Edit form for a :class:`~blog.models.Product` (without bullets — see :class:`ProductBulletForm`)."""

    class Meta:
        model = Product
        fields = [
            'slug', 'name_en', 'name_uz', 'kind_en', 'kind_uz',
            'price_en', 'price_uz', 'blurb_en', 'blurb_uz',
            'content_en', 'content_uz', 'cta_en', 'cta_uz', 'checkout_url', 'order',
        ]
        widgets = {
            'slug': forms.TextInput(attrs={'class': _INPUT}),
            'name_en': forms.TextInput(attrs={'class': _INPUT}),
            'name_uz': forms.TextInput(attrs={'class': _INPUT}),
            'kind_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Course, SaaS, eBook...'}),
            'kind_uz': forms.TextInput(attrs={'class': _INPUT}),
            'price_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': '$24'}),
            'price_uz': forms.TextInput(attrs={'class': _INPUT}),
            'blurb_en': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'blurb_uz': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'content_en': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 15}),
            'content_uz': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 15}),
            'cta_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Buy now'}),
            'cta_uz': forms.TextInput(attrs={'class': _INPUT}),
            'checkout_url': forms.URLInput(attrs={'class': _INPUT, 'placeholder': 'https://buy.stripe.com/...'}),
            'order': forms.NumberInput(attrs={'class': _INPUT}),
        }


class ProductBulletForm(forms.ModelForm):
    """Bullet rows are managed inline by the product template, but this form
    is provided in case anyone wants a stand-alone editor in the future."""

    class Meta:
        model = ProductBullet
        fields = ['text_en', 'text_uz', 'order']
        widgets = {
            'text_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Bullet point (English)'}),
            'text_uz': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Bullet point (Uzbek)'}),
            'order': forms.NumberInput(attrs={'class': _INPUT, 'style': 'width:80px'}),
        }


class NewsletterIssueForm(forms.ModelForm):
    class Meta:
        model = NewsletterIssue
        fields = ['number', 'date_en', 'date_uz', 'title_en', 'title_uz', 'content_en', 'content_uz']
        widgets = {
            'number': forms.NumberInput(attrs={'class': _INPUT}),
            'date_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'April 2026'}),
            'date_uz': forms.TextInput(attrs={'class': _INPUT, 'placeholder': '2026 aprel'}),
            'title_en': forms.TextInput(attrs={'class': _INPUT}),
            'title_uz': forms.TextInput(attrs={'class': _INPUT}),
            'content_en': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 15}),
            'content_uz': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 15}),
        }


class UsesCategoryForm(forms.ModelForm):
    class Meta:
        model = UsesCategory
        fields = ['title_en', 'title_uz', 'order']
        widgets = {
            'title_en': forms.TextInput(attrs={'class': _INPUT}),
            'title_uz': forms.TextInput(attrs={'class': _INPUT}),
            'order': forms.NumberInput(attrs={'class': _INPUT}),
        }


class UsesItemForm(forms.ModelForm):
    class Meta:
        model = UsesItem
        fields = ['category', 'name', 'note_en', 'note_uz', 'order']
        widgets = {
            'category': forms.Select(attrs={'class': _SELECT}),
            'name': forms.TextInput(attrs={'class': _INPUT}),
            'note_en': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'note_uz': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': _INPUT}),
        }


class TimelineEntryForm(forms.ModelForm):
    class Meta:
        model = TimelineEntry
        fields = ['period_en', 'period_uz', 'description_en', 'description_uz', 'order']
        widgets = {
            'period_en': forms.TextInput(attrs={'class': _INPUT, 'placeholder': '2024 — now'}),
            'period_uz': forms.TextInput(attrs={'class': _INPUT, 'placeholder': '2024 — hozir'}),
            'description_en': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'description_uz': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': _INPUT}),
        }


class SiteSettingsForm(forms.ModelForm):
    """Edit the singleton settings row from the dashboard."""

    class Meta:
        model = SiteSettings
        fields = [
            'site_url', 'analytics_domain', 'giscus_repo', 'giscus_repo_id',
            'giscus_category_id', 'calendly_url', 'double_opt_in', 'comments_enabled',
        ]
        widgets = {
            'site_url': forms.URLInput(attrs={'class': _INPUT}),
            'analytics_domain': forms.TextInput(attrs={'class': _INPUT}),
            'giscus_repo': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'user/repo'}),
            'giscus_repo_id': forms.TextInput(attrs={'class': _INPUT}),
            'giscus_category_id': forms.TextInput(attrs={'class': _INPUT}),
            'calendly_url': forms.URLInput(attrs={'class': _INPUT}),
            'double_opt_in': forms.CheckboxInput(attrs={'class': _CHECKBOX}),
            'comments_enabled': forms.CheckboxInput(attrs={'class': _CHECKBOX}),
        }


class NowPageForm(forms.ModelForm):
    class Meta:
        model = NowPage
        fields = ['content_en', 'content_uz', 'content_format']
        widgets = {
            'content_en': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 12}),
            'content_uz': forms.Textarea(attrs={'class': _TEXTAREA_TALL, 'rows': 12}),
            'content_format': forms.Select(attrs={'class': _SELECT}),
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'role_en', 'role_uz', 'quote_en', 'quote_uz', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': _INPUT}),
            'role_en': forms.TextInput(attrs={'class': _INPUT}),
            'role_uz': forms.TextInput(attrs={'class': _INPUT}),
            'quote_en': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'quote_uz': forms.Textarea(attrs={'class': _TEXTAREA, 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': _INPUT}),
        }
