"""Signal handlers for the blog app.

Right now the only handler we need is image optimisation: when an editor
uploads a featured image we resize and re-encode it before it hits the disk.
That keeps page weight predictable regardless of what the editor uploads
(camera-original PNGs, 4K screenshots, etc.).
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Post
from .utils import optimize_image_field


@receiver(pre_save, sender=Post)
def optimize_post_image(sender, instance: Post, **kwargs) -> None:
    """Optimise ``Post.featured_image`` before it is persisted.

    We compare the in-memory instance against the database row so that we
    only re-process when the image has actually changed.  On creation we
    always run the optimiser.
    """
    # New row: nothing to compare against, optimise the upload directly.
    if not instance.pk:
        optimize_image_field(instance.featured_image)
        return

    # Existing row: compare the previous value to the incoming one. If the
    # editor only changed text we skip the (costly) Pillow round-trip.
    try:
        old = Post.objects.get(pk=instance.pk)
    except Post.DoesNotExist:
        # Race condition (object deleted between get and save): optimise
        # anyway — nothing to lose.
        optimize_image_field(instance.featured_image)
        return

    if old.featured_image != instance.featured_image:
        optimize_image_field(instance.featured_image)
