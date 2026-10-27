from budgeting.currency import fetch_exchange_rates

from .models import UserProfile


def _resolve_nav_section(request) -> str:
    match = getattr(request, 'resolver_match', None)
    if match is None:
        return ''
    name = match.url_name or ''
    namespace = match.namespace or ''

    if namespace == 'sitepages':
        return name or 'about'

    if namespace == 'accounts':
        if name.startswith('settings') or name in {
            'password_change',
            'password_change_done',
            'delete_account',
            'dismiss_onboarding',
            'password_reset',
            'password_reset_done',
            'password_reset_confirm',
            'password_reset_complete',
        }:
            return 'settings'
        if name in {'login', 'register'}:
            return name
        return 'settings'

    if name in {'home', 'dashboard'}:
        return 'home' if name == 'home' else 'dashboard'
    if name == 'system_overview':
        return 'overview'
    if name in {'reports'}:
        return 'reports'
    if name in {'insights'}:
        return 'insights'
    if name.startswith('help'):
        return 'help'
    if name.startswith('transaction'):
        return 'transactions'
    if name.startswith('category') or name.startswith('tag'):
        return 'categories'
    if name.startswith('budget'):
        return 'budgets'
    if name.startswith('goal'):
        return 'goals'
    return ''


def user_settings(request):
    currency = UserProfile.Currency.UAH
    rates_payload = {
        'rates': {},
        'source': None,
        'fetched_at': None,
        'next_refresh_at': None,
    }

    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile is None:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
        currency = profile.preferred_currency
        # Курси потрібні лише авторизованим (відображення сум) — не на публічному лендінгу.
        rates_payload = fetch_exchange_rates(force=False)

    return {
        'display_currency': currency,
        'exchange_rates': rates_payload['rates'],
        'rates_source': rates_payload['source'],
        'rates_fetched_at': rates_payload.get('fetched_at'),
        'rates_next_refresh_at': rates_payload.get('next_refresh_at'),
        'nav_section': _resolve_nav_section(request),
    }
