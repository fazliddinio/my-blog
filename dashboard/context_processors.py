"""Context processors for the dashboard.

A single helper exposes "unread messages" and "subscriber count" badges
to the dashboard sidebar without each view having to compute them.
"""

from blog.models import ContactMessage, NewsletterSubscriber


def dashboard_counts(request):
    """Surface badge counters used in the dashboard sidebar.

    Returns an empty dict for non-dashboard requests (or anonymous users),
    keeping the public site free of unrelated DB queries.
    """
    # Only do the work for authenticated dashboard requests.
    if not request.path.startswith('/dashboard/') or not request.user.is_authenticated:
        return {}

    return {
        'unread_messages_count': ContactMessage.objects.filter(is_read=False).count(),
        'subscribers_count': NewsletterSubscriber.objects.filter(is_active=True).count(),
    }
