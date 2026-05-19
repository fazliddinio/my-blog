"""Custom Django ORM managers used by the blog app.

The single most important guarantee in this file is *defence in depth* against
draft posts leaking onto the public site:

``Post.published.all()`` — and therefore every queryset reachable from
``Post.published`` — will *only* return rows that are
status-published *and* whose ``published_at`` is in the past.

Public views are written against ``Post.published`` so a missing filter in a
view cannot accidentally surface a draft.
"""

from django.db import models
from django.utils import timezone


class PublishedPostQuerySet(models.QuerySet):
    """QuerySet that knows how to narrow itself to publicly-visible posts."""

    def published(self):
        """Return rows that are published *and* not scheduled for the future.

        ``published_at`` is allowed to be ``NULL`` (legacy rows from before
        the column was added); these are always visible. Future-dated rows
        are scheduled posts and are hidden until their time arrives.
        """
        now = timezone.now()
        return self.filter(status='published').filter(
            models.Q(published_at__isnull=True) | models.Q(published_at__lte=now)
        )


class PublishedPostManager(models.Manager):
    """Manager whose default queryset is already filtered to public posts.

    Using this as ``Post.published`` means *every* lookup — including
    ``Post.published.filter(...)`` and ``Post.published.get(...)`` — is
    automatically scoped to rows the public is allowed to see.
    """

    def get_queryset(self):
        return PublishedPostQuerySet(self.model, using=self._db).published()
