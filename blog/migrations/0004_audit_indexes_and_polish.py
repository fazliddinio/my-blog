from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_nowpage_sitesettings_testimonial_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='tag',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='post',
            name='read_time',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Reading time (minutes); auto-calculated if left blank.',
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='featured',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='post',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published')],
                db_index=True,
                default='published',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='published_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='series',
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='post',
            name='content_format',
            field=models.CharField(
                choices=[('html', 'HTML'), ('markdown', 'Markdown')],
                default='markdown',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='content_en',
            field=models.TextField(blank=True, help_text='Full body (English)'),
        ),
        migrations.AlterField(
            model_name='post',
            name='content_uz',
            field=models.TextField(blank=True, help_text='Full body (Uzbek)'),
        ),
        migrations.AlterField(
            model_name='post',
            name='dek_en',
            field=models.TextField(help_text='Short description (English)'),
        ),
        migrations.AlterField(
            model_name='post',
            name='dek_uz',
            field=models.TextField(blank=True, help_text='Short description (Uzbek)'),
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-date', '-published_at']},
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['status', '-date'], name='blog_post_status_3a9020_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['featured', '-date'], name='blog_post_feature_06c2d8_idx'),
        ),
        migrations.AlterField(
            model_name='newslettersubscriber',
            name='confirm_token',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='newslettersubscriber',
            name='unsubscribe_token',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='newsletterissue',
            name='date_en',
            field=models.CharField(help_text='Display date, e.g. April 2026', max_length=50),
        ),
        migrations.AlterField(
            model_name='newsletterissue',
            name='content_en',
            field=models.TextField(blank=True, help_text='Issue body (HTML or Markdown)'),
        ),
        migrations.AddField(
            model_name='newsletterissue',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='contactmessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='content_en',
            field=models.TextField(blank=True, help_text='Body (HTML or Markdown)'),
        ),
        migrations.AlterField(
            model_name='product',
            name='content_uz',
            field=models.TextField(blank=True, help_text='Body (HTML or Markdown)'),
        ),
        migrations.AlterField(
            model_name='project',
            name='href',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AlterField(
            model_name='usesitem',
            name='note_en',
            field=models.TextField(blank=True),
        ),
    ]
