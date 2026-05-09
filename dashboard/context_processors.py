from blog.models import ContactMessage, NewsletterSubscriber


def dashboard_counts(request):
    if not request.path.startswith('/dashboard/') or not request.user.is_authenticated:
        return {}
    return {
        'unread_messages_count': ContactMessage.objects.filter(is_read=False).count(),
        'subscribers_count': NewsletterSubscriber.objects.filter(is_active=True).count(),
    }
