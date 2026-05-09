from django import forms
from blog.models import (
    Post, Project, Product, ProductBullet,
    NewsletterIssue, UsesCategory, UsesItem, TimelineEntry,
)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title_en', 'title_uz', 'slug', 'date', 'tag', 'read_time',
            'dek_en', 'dek_uz', 'content_en', 'content_uz', 'featured',
        ]
        widgets = {
            'title_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'Post title (English)'}),
            'title_uz': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'Post title (Uzbek)'}),
            'slug': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'auto-generated-slug'}),
            'date': forms.DateInput(attrs={'class': 'dash-form__input', 'type': 'date'}),
            'tag': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'e.g. caching, react, career'}),
            'read_time': forms.NumberInput(attrs={'class': 'dash-form__input', 'placeholder': '8'}),
            'dek_en': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3, 'placeholder': 'Short description (English)'}),
            'dek_uz': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3, 'placeholder': 'Short description (Uzbek)'}),
            'content_en': forms.Textarea(attrs={'class': 'dash-form__textarea dash-form__textarea--tall', 'rows': 20, 'placeholder': 'Full post body (HTML supported)'}),
            'content_uz': forms.Textarea(attrs={'class': 'dash-form__textarea dash-form__textarea--tall', 'rows': 20, 'placeholder': 'Full post body in Uzbek (HTML supported)'}),
            'featured': forms.CheckboxInput(attrs={'class': 'dash-form__checkbox'}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'tagline_en', 'tagline_uz', 'desc_en', 'desc_uz', 'language', 'stars', 'href', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'tagline_en': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'tagline_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'desc_en': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'desc_uz': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'language': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'TypeScript, Go, Python...'}),
            'stars': forms.NumberInput(attrs={'class': 'dash-form__input'}),
            'href': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'https://github.com/...'}),
            'order': forms.NumberInput(attrs={'class': 'dash-form__input'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'slug', 'name_en', 'name_uz', 'kind_en', 'kind_uz',
            'price_en', 'price_uz', 'blurb_en', 'blurb_uz',
            'content_en', 'content_uz', 'cta_en', 'cta_uz', 'order',
        ]
        widgets = {
            'slug': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'name_en': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'name_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'kind_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'Course, SaaS, eBook...'}),
            'kind_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'price_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': '$24'}),
            'price_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'blurb_en': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'blurb_uz': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'content_en': forms.Textarea(attrs={'class': 'dash-form__textarea dash-form__textarea--tall', 'rows': 15}),
            'content_uz': forms.Textarea(attrs={'class': 'dash-form__textarea dash-form__textarea--tall', 'rows': 15}),
            'cta_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'Buy now'}),
            'cta_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'order': forms.NumberInput(attrs={'class': 'dash-form__input'}),
        }


class ProductBulletForm(forms.ModelForm):
    class Meta:
        model = ProductBullet
        fields = ['text_en', 'text_uz', 'order']
        widgets = {
            'text_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'Bullet point (English)'}),
            'text_uz': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'Bullet point (Uzbek)'}),
            'order': forms.NumberInput(attrs={'class': 'dash-form__input', 'style': 'width:80px'}),
        }


class NewsletterIssueForm(forms.ModelForm):
    class Meta:
        model = NewsletterIssue
        fields = ['number', 'date_en', 'date_uz', 'title_en', 'title_uz', 'content_en', 'content_uz']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'dash-form__input'}),
            'date_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': 'April 2026'}),
            'date_uz': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': '2026 aprel'}),
            'title_en': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'title_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'content_en': forms.Textarea(attrs={'class': 'dash-form__textarea dash-form__textarea--tall', 'rows': 15}),
            'content_uz': forms.Textarea(attrs={'class': 'dash-form__textarea dash-form__textarea--tall', 'rows': 15}),
        }


class UsesCategoryForm(forms.ModelForm):
    class Meta:
        model = UsesCategory
        fields = ['title_en', 'title_uz', 'order']
        widgets = {
            'title_en': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'title_uz': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'order': forms.NumberInput(attrs={'class': 'dash-form__input'}),
        }


class UsesItemForm(forms.ModelForm):
    class Meta:
        model = UsesItem
        fields = ['category', 'name', 'note_en', 'note_uz', 'order']
        widgets = {
            'category': forms.Select(attrs={'class': 'dash-form__select'}),
            'name': forms.TextInput(attrs={'class': 'dash-form__input'}),
            'note_en': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'note_uz': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'dash-form__input'}),
        }


class TimelineEntryForm(forms.ModelForm):
    class Meta:
        model = TimelineEntry
        fields = ['period_en', 'period_uz', 'description_en', 'description_uz', 'order']
        widgets = {
            'period_en': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': '2024 — now'}),
            'period_uz': forms.TextInput(attrs={'class': 'dash-form__input', 'placeholder': '2024 — hozir'}),
            'description_en': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'description_uz': forms.Textarea(attrs={'class': 'dash-form__textarea', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'dash-form__input'}),
        }
