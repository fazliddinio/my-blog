from django.db import migrations, models
from django.utils.text import slugify


def populate_product_slugs(apps, schema_editor):
    Product = apps.get_model('blog', 'Product')
    for p in Product.objects.all():
        p.slug = slugify(p.name_en)
        p.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsletterissue',
            name='content_en',
            field=models.TextField(blank=True, help_text='Issue body (English, HTML)'),
        ),
        migrations.AddField(
            model_name='newsletterissue',
            name='content_uz',
            field=models.TextField(blank=True, help_text='Issue body (Uzbek, HTML)'),
        ),
        migrations.AddField(
            model_name='product',
            name='content_en',
            field=models.TextField(blank=True, help_text='Full product page body (English, HTML)'),
        ),
        migrations.AddField(
            model_name='product',
            name='content_uz',
            field=models.TextField(blank=True, help_text='Full product page body (Uzbek, HTML)'),
        ),
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(populate_product_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='href',
            field=models.CharField(blank=True, default='#', max_length=500),
        ),
    ]
