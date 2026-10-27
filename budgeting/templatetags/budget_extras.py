from django import template

from budgeting.currency import format_money

register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Збирає поточний GET-рядок і підставляє/скидає ключі (для пагінації з фільтрами)."""
    request = context.get('request')
    if request is None:
        return ''
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == '':
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()


@register.simple_tag(takes_context=True)
def uah(context, amount):
    """Форматує суму з урахуванням валюти з налаштувань користувача."""
    currency = context.get('display_currency') or 'UAH'
    try:
        return format_money(amount, currency)
    except (TypeError, ValueError):
        return format_money(0, currency)


@register.simple_tag
def money(amount, currency='UAH'):
    """Явне форматування суми в заданій валюті."""
    try:
        return format_money(amount, currency)
    except (TypeError, ValueError):
        return format_money(0, currency)


@register.inclusion_tag('budgeting/includes/progress_bar.html')
def budget_progress_bar(percent, over=False):
    """Inclusion-tag: смуга прогресу бюджету/цілі (HTML з templates/...)."""
    try:
        # кругле число без коми — інакше uk-локаль ламає CSS width: 23,5%
        value = round(max(0.0, min(float(percent), 100.0)), 2)
    except (TypeError, ValueError):
        value = 0.0
    if over or value >= 100:
        css = 'bg-danger'
    elif value < 80:
        css = 'bg-success'
    else:
        css = 'bg-warning'
    return {'percent': value, 'bar_class': css}
