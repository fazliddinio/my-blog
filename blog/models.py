from django.db import models
from django.utils.text import slugify


class Post(models.Model):
    slug = models.SlugField(max_length=200, unique=True)
    date = models.DateField()
    title_en = models.CharField(max_length=300)
    title_uz = models.CharField(max_length=300, blank=True)
    dek_en = models.TextField(help_text="Short description / deck (English)")
    dek_uz = models.TextField(blank=True, help_text="Short description / deck (Uzbek)")
    tag = models.CharField(max_length=50)
    read_time = models.PositiveIntegerField(help_text="Estimated reading time in minutes")
    featured = models.BooleanField(default=False)
    content_en = models.TextField(blank=True, help_text="Full post body (English, supports HTML)")
    content_uz = models.TextField(blank=True, help_text="Full post body (Uzbek, supports HTML)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title_en

    @property
    def year(self):
        return self.date.year

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_en)
        super().save(*args, **kwargs)


class Project(models.Model):
    name = models.CharField(max_length=100)
    tagline_en = models.CharField(max_length=300)
    tagline_uz = models.CharField(max_length=300, blank=True)
    desc_en = models.TextField()
    desc_uz = models.TextField(blank=True)
    stars = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=50)
    href = models.CharField(max_length=500, blank=True, default='#')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

    @property
    def lang_color(self):
        colors = {
            'TypeScript': '#3178c6',
            'Go': '#00add8',
            'Python': '#3572a5',
            'Swift': '#f05138',
        }
        return colors.get(self.language, '#666')


class UsesCategory(models.Model):
    title_en = models.CharField(max_length=100)
    title_uz = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Uses categories'

    def __str__(self):
        return self.title_en


class UsesItem(models.Model):
    category = models.ForeignKey(UsesCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    note_en = models.TextField()
    note_uz = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Product(models.Model):
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    name_en = models.CharField(max_length=200)
    name_uz = models.CharField(max_length=200, blank=True)
    kind_en = models.CharField(max_length=50)
    kind_uz = models.CharField(max_length=50, blank=True)
    price_en = models.CharField(max_length=50)
    price_uz = models.CharField(max_length=50, blank=True)
    blurb_en = models.TextField()
    blurb_uz = models.TextField(blank=True)
    content_en = models.TextField(blank=True, help_text="Full product page body (English, HTML)")
    content_uz = models.TextField(blank=True, help_text="Full product page body (Uzbek, HTML)")
    cta_en = models.CharField(max_length=50)
    cta_uz = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name_en

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name_en)
        super().save(*args, **kwargs)


class ProductBullet(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bullets')
    text_en = models.CharField(max_length=200)
    text_uz = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text_en


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


class NewsletterIssue(models.Model):
    number = models.PositiveIntegerField(unique=True)
    date_en = models.CharField(max_length=50)
    date_uz = models.CharField(max_length=50, blank=True)
    title_en = models.CharField(max_length=300)
    title_uz = models.CharField(max_length=300, blank=True)
    content_en = models.TextField(blank=True, help_text="Issue body (English, HTML)")
    content_uz = models.TextField(blank=True, help_text="Issue body (Uzbek, HTML)")

    class Meta:
        ordering = ['-number']

    def __str__(self):
        return f"Issue #{self.number}"


class ContactMessage(models.Model):
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} — {self.created_at:%Y-%m-%d}"


class TimelineEntry(models.Model):
    period_en = models.CharField(max_length=100)
    period_uz = models.CharField(max_length=100, blank=True)
    description_en = models.TextField()
    description_uz = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Timeline entries'

    def __str__(self):
        return self.period_en
