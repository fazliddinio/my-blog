"""Django application config for the public ``blog`` app.

The ``ready`` hook imports the signals module so that the ``pre_save``
handler in :mod:`blog.signals` is registered exactly once on startup.
"""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self) -> None:
        # Importing the module registers all ``@receiver`` decorators.
        # The ``noqa`` is intentional: the import is for its side effects.
        import blog.signals  # noqa: F401
