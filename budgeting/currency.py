"""Курси валют: НБУ + ПриватБанк + Monobank; купівля/продаж для всіх підтримуваних.

Кеш ~30 хв — щоб курс не стрибав на кожному оновленні сторінки.
Якщо API недоступні — повертаємо останній вдалий знімок (до 24 год).
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.utils import timezone

KYIV = ZoneInfo('Europe/Kyiv')

logger = logging.getLogger(__name__)

NBU_URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'
PRIVATBANK_URL = 'https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5'
MONOBANK_URL = 'https://api.monobank.ua/bank/currency'

CACHE_KEY = 'exchange_rates_v5'
STALE_KEY = 'exchange_rates_v5_stale'
# основний кеш: курс стабільний між оновленнями сторінки
CACHE_TTL_SECONDS = 30 * 60  # 30 хвилин
# запасний знімок, якщо всі API впали
STALE_TTL_SECONDS = 24 * 60 * 60  # 24 години

SUPPORTED_CODES = (
    'USD', 'EUR', 'GBP', 'PLN', 'CHF', 'CZK', 'CAD', 'CNY', 'JPY', 'TRY', 'AUD', 'RON',
)

ISO_NUMERIC_TO_CODE = {
    840: 'USD',
    978: 'EUR',
    826: 'GBP',
    985: 'PLN',
    756: 'CHF',
    203: 'CZK',
    124: 'CAD',
    156: 'CNY',
    392: 'JPY',
    949: 'TRY',
    36: 'AUD',
    946: 'RON',
    980: 'UAH',
}

CURRENCY_SYMBOLS = {
    'UAH': '₴',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'PLN': 'zł',
    'CHF': 'Fr',
    'CZK': 'Kč',
    'CAD': 'C$',
    'CNY': '¥',
    'JPY': '¥',
    'TRY': '₺',
    'AUD': 'A$',
    'RON': 'lei',
}

FALLBACK_RATES = {
    'USD': Decimal('41.50'),
    'EUR': Decimal('45.20'),
    'GBP': Decimal('53.00'),
    'PLN': Decimal('10.50'),
    'CHF': Decimal('48.00'),
    'CZK': Decimal('1.85'),
    'CAD': Decimal('29.50'),
    'CNY': Decimal('5.80'),
    'JPY': Decimal('0.28'),
    'TRY': Decimal('1.20'),
    'AUD': Decimal('27.00'),
    'RON': Decimal('9.10'),
}

SPREAD = Decimal('0.008')  # ±0.8% якщо банк не дає окремий buy/sell


def _http_json(url: str) -> list | dict:
    req = urllib.request.Request(url, headers={'User-Agent': 'FinanceHelper/1.0'})
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode('utf-8'))


def _spread_from_mid(mid: Decimal) -> tuple[Decimal, Decimal]:
    buy = (mid * (Decimal('1') - SPREAD)).quantize(Decimal('0.0001'))
    sale = (mid * (Decimal('1') + SPREAD)).quantize(Decimal('0.0001'))
    return buy, sale


def _empty_rates() -> dict:
    return {
        code: {
            'rate': value,
            'buy': None,
            'sale': None,
            'base': 'UAH',
            'name': code,
            'quote': 'fallback',
        }
        for code, value in FALLBACK_RATES.items()
    }


def _stamp_times(payload: dict) -> dict:
    """Додає час оновлення та наступного оновлення з точністю до хвилини."""
    now = timezone.now().astimezone(KYIV)
    iso = payload.get('fetched_at_iso')
    if iso:
        try:
            fetched = datetime.fromisoformat(iso)
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=KYIV)
            else:
                fetched = fetched.astimezone(KYIV)
        except (TypeError, ValueError):
            fetched = now
            iso = now.isoformat()
    else:
        fetched = now
        iso = now.isoformat()

    next_at = fetched + timedelta(seconds=CACHE_TTL_SECONDS)
    payload['fetched_at_iso'] = iso
    payload['fetched_at'] = fetched.strftime('%H:%M')
    payload['next_refresh_at'] = next_at.strftime('%H:%M')
    return payload


def _serialize_rates(payload: dict) -> dict:
    """Decimal → str для надійного LocMem/JSON-кешу."""
    payload = _stamp_times(dict(payload))
    out = {
        'source': payload['source'],
        'fetched_at': payload['fetched_at'],
        'fetched_at_iso': payload['fetched_at_iso'],
        'next_refresh_at': payload['next_refresh_at'],
        'rates': {},
    }
    for code, row in payload['rates'].items():
        out['rates'][code] = {
            'rate': str(row['rate']) if row.get('rate') is not None else None,
            'buy': str(row['buy']) if row.get('buy') is not None else None,
            'sale': str(row['sale']) if row.get('sale') is not None else None,
            'base': row.get('base', 'UAH'),
            'name': row.get('name', code),
            'quote': row.get('quote', 'fallback'),
        }
    return out


def _deserialize_rates(payload: dict) -> dict:
    out = {
        'source': payload.get('source', 'fallback'),
        'fetched_at': payload.get('fetched_at', ''),
        'fetched_at_iso': payload.get('fetched_at_iso', ''),
        'next_refresh_at': payload.get('next_refresh_at', ''),
        'rates': {},
    }
    for code, row in (payload.get('rates') or {}).items():
        out['rates'][code] = {
            'rate': Decimal(row['rate']) if row.get('rate') is not None else None,
            'buy': Decimal(row['buy']) if row.get('buy') is not None else None,
            'sale': Decimal(row['sale']) if row.get('sale') is not None else None,
            'base': row.get('base', 'UAH'),
            'name': row.get('name', code),
            'quote': row.get('quote', 'fallback'),
        }
    return _stamp_times(out)


def _apply_nbu(rates: dict) -> str | None:
    payload = _http_json(NBU_URL)
    touched = False
    for item in payload:
        code = (item.get('cc') or '').upper()
        if code not in rates:
            continue
        rates[code]['rate'] = Decimal(str(item['rate']))
        rates[code]['name'] = item.get('txt') or code
        if rates[code].get('quote') == 'fallback':
            rates[code]['quote'] = 'nbu'
        touched = True
    return 'nbu' if touched else None


def _apply_privatbank(rates: dict) -> str | None:
    payload = _http_json(PRIVATBANK_URL)
    touched = False
    for item in payload:
        code = (item.get('ccy') or '').upper()
        if code not in rates:
            continue
        buy = Decimal(str(item['buy']))
        sale = Decimal(str(item['sale']))
        rates[code]['buy'] = buy
        rates[code]['sale'] = sale
        rates[code]['quote'] = 'privatbank'
        # mid для конвертації сум — стабільніше, ніж лише sale
        rates[code]['rate'] = ((buy + sale) / 2).quantize(Decimal('0.0001'))
        touched = True
    return 'privatbank' if touched else None


def _apply_monobank(rates: dict) -> str | None:
    payload = _http_json(MONOBANK_URL)
    touched = False
    for row in payload:
        if row.get('currencyCodeB') != 980:
            continue
        code = ISO_NUMERIC_TO_CODE.get(row.get('currencyCodeA'))
        if not code or code not in rates:
            continue
        buy = row.get('rateBuy')
        sell = row.get('rateSell')
        cross = row.get('rateCross')
        if buy is not None and sell is not None:
            b = Decimal(str(buy))
            s = Decimal(str(sell))
            rates[code]['buy'] = b
            rates[code]['sale'] = s
            rates[code]['quote'] = 'monobank'
            rates[code]['rate'] = ((b + s) / 2).quantize(Decimal('0.0001'))
            touched = True
        elif cross is not None and rates[code]['buy'] is None:
            mid = Decimal(str(cross))
            b, s = _spread_from_mid(mid)
            rates[code]['buy'] = b
            rates[code]['sale'] = s
            rates[code]['quote'] = 'monobank_cross'
            rates[code]['rate'] = mid
            touched = True
    return 'monobank' if touched else None


def _fill_missing_buy_sale(rates: dict) -> None:
    for code, row in rates.items():
        if row['buy'] is not None and row['sale'] is not None:
            continue
        mid = row.get('rate') or FALLBACK_RATES.get(code) or Decimal('1')
        buy, sale = _spread_from_mid(Decimal(mid))
        row['buy'] = buy
        row['sale'] = sale
        if row.get('quote') in (None, 'fallback'):
            row['quote'] = 'estimated'


def _live_fetch() -> dict | None:
    """Послідовне завантаження (без гонок між потоками)."""
    rates = _empty_rates()
    sources: list[str] = []

    for name, loader in (
        ('nbu', _apply_nbu),
        ('privatbank', _apply_privatbank),
        ('monobank', _apply_monobank),
    ):
        try:
            label = loader(rates)
            if label:
                sources.append(label)
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
            TypeError,
        ) as exc:
            logger.warning('%s API недоступне: %s', name, exc)

    if not sources:
        return None

    _fill_missing_buy_sale(rates)
    now = timezone.now().astimezone(KYIV)
    return _stamp_times({
        'rates': rates,
        'source': '+'.join(sources),
        'fetched_at_iso': now.isoformat(),
    })


def _fallback_payload() -> dict:
    rates = _empty_rates()
    _fill_missing_buy_sale(rates)
    now = timezone.now().astimezone(KYIV)
    return _stamp_times({
        'rates': rates,
        'source': 'fallback',
        'fetched_at_iso': now.isoformat(),
    })


def fetch_exchange_rates(*, force: bool = False) -> dict:
    if not force:
        cached = cache.get(CACHE_KEY)
        if cached:
            return _deserialize_rates(cached)

    live = _live_fetch()
    if live is not None:
        serialized = _serialize_rates(live)
        cache.set(CACHE_KEY, serialized, CACHE_TTL_SECONDS)
        cache.set(STALE_KEY, serialized, STALE_TTL_SECONDS)
        return live

    # API впали — спочатку свіжий кеш (міг з’явитись паралельно), потім stale
    for key in (CACHE_KEY, STALE_KEY):
        stale = cache.get(key)
        if stale:
            result = _deserialize_rates(stale)
            result['source'] = f"{result.get('source', 'cache')}+stale"
            return result

    return _fallback_payload()


def get_rate_to_uah(currency: str) -> Decimal:
    currency = (currency or 'UAH').upper()
    if currency == 'UAH':
        return Decimal('1')
    data = fetch_exchange_rates()
    row = data['rates'].get(currency) or {}
    # mid (rate) стабільніший за sale для відображення сум
    rate = row.get('rate') or row.get('sale') or Decimal('1')
    return rate if rate > 0 else Decimal('1')


def convert_from_uah(amount, currency: str) -> Decimal:
    value = Decimal(str(amount or 0))
    currency = (currency or 'UAH').upper()
    if currency == 'UAH':
        return value.quantize(Decimal('0.01'))
    rate = get_rate_to_uah(currency)
    if rate <= 0:
        return value.quantize(Decimal('0.01'))
    quant = Decimal('0.01') if currency != 'JPY' else Decimal('1')
    return (value / rate).quantize(quant)


def convert_to_uah(amount, currency: str) -> Decimal:
    """Сума, введена в валюті відображення → гривні для збереження в БД."""
    value = Decimal(str(amount or 0))
    currency = (currency or 'UAH').upper()
    if currency == 'UAH':
        return value.quantize(Decimal('0.01'))
    rate = get_rate_to_uah(currency)
    if rate <= 0:
        return value.quantize(Decimal('0.01'))
    return (value * rate).quantize(Decimal('0.01'))


def get_user_display_currency(user) -> str:
    if user is None or not getattr(user, 'is_authenticated', False):
        return 'UAH'
    profile = getattr(user, 'profile', None)
    if profile is None:
        return 'UAH'
    return profile.preferred_currency or 'UAH'


def format_money(amount, currency: str = 'UAH') -> str:
    currency = (currency or 'UAH').upper()
    converted = convert_from_uah(amount, currency)
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency == 'JPY':
        number = f'{float(converted):,.0f}'.replace(',', ' ')
    else:
        number = f'{float(converted):,.2f}'.replace(',', ' ')
    return f'{symbol} {number}'
