"""Template tags & filters for rendering post / now-page bodies.

These wrap :func:`blog.utils.render_content` so templates don't have to
import or know about it. Every helper that returns HTML marks the result
safe — the underlying Markdown renderer escapes user input, and
HTML bodies are author-controlled (admin-only).
"""

from django import template
from django.utils.safestring import mark_safe

from blog.utils import extract_toc, inject_heading_ids, render_content

register = template.Library()


@register.simple_tag
def post_content(post, lang: str = 'en'):
    """Render a post body for the requested language.

    Falls back to English when an Uzbek translation is missing. The output
    has ``id`` attributes on ``<h2>`` / ``<h3>`` headings so the table of
    contents and deep-links work out of the box.
    """
    raw = post.content_uz if lang == 'uz' and post.content_uz else post.content_en
    html = render_content(raw, post.content_format)
    html = inject_heading_ids(html)
    return mark_safe(html)


@register.simple_tag
def post_toc(post, lang: str = 'en'):
    """Return a list of ``{level, id, title}`` dicts for the post's headings.

    Templates render this into a ``<nav>`` near the top of long essays.
    """
    raw = post.content_uz if lang == 'uz' and post.content_uz else post.content_en
    html = render_content(raw, post.content_format)
    html = inject_heading_ids(html)
    return extract_toc(html)


@register.filter
def render_markdown_or_html(raw: str, content_format: str = 'html'):
    """Filter equivalent of :func:`post_content` for ad-hoc bodies.

    Useful for the ``Now`` page and newsletter issue templates, which render
    a body but don't have the surrounding ``Post`` object.
    """
    return mark_safe(render_content(raw or '', content_format))
