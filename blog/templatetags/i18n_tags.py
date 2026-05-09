from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def tr(context, en_text, uz_text=''):
    """Return English or Uzbek text based on current language cookie."""
    request = context.get('request')
    lang = 'en'
    if request:
        lang = request.COOKIES.get('fz_lang', 'en')
    if lang == 'uz' and uz_text:
        return uz_text
    return en_text


@register.filter
def bilingual(obj, field_base):
    """Usage: {{ post|bilingual:'title' }} — picks title_en or title_uz."""
    return getattr(obj, field_base, '')


@register.simple_tag(takes_context=True)
def get_lang(context):
    request = context.get('request')
    if request:
        return request.COOKIES.get('fz_lang', 'en')
    return 'en'


@register.simple_tag(takes_context=True)
def bi(context, obj, field_base):
    """Usage: {% bi post 'title' %} — returns title_en or title_uz based on cookie."""
    request = context.get('request')
    lang = 'en'
    if request:
        lang = request.COOKIES.get('fz_lang', 'en')
    val = getattr(obj, f'{field_base}_{lang}', '')
    if not val:
        val = getattr(obj, f'{field_base}_en', '')
    return val
