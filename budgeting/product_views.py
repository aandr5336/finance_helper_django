"""Звіти, insights, календар, довідка, CSV — «глибина» продукту."""

from __future__ import annotations

import calendar
import csv
import io
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Budget, Category, SavingsGoal, Transaction

HELP_ARTICLES = {
    'start': {
        'title': 'Швидкий старт',
        'body': (
            '1) Створіть кілька категорій доходів і витрат.\n'
            '2) Додайте перші транзакції.\n'
            '3) Задайте бюджет на місяць і ціль заощаджень.\n'
            '4) У налаштуваннях оберіть валюту відображення.'
        ),
    },
    'currency': {
        'title': 'Валюти і курси',
        'body': (
            'Суми в базі завжди в гривнях. Обрана валюта змінює лише відображення.\n'
            'Курси кешуються ~30 хвилин; примусове оновлення — у Налаштуваннях → Валюта.'
        ),
    },
    'budgets': {
        'title': 'Бюджети',
        'body': (
            'Бюджет — ліміт на категорію витрат за місяць.\n'
            'Якщо додаєте бюджет на ту саму категорію й місяць повторно — сума додається до існуючого.'
        ),
    },
    'csv': {
        'title': 'Імпорт і експорт CSV',
        'body': (
            'Експорт: Налаштування → Дані → Завантажити CSV.\n'
            'Імпорт: колонки date,type,category,amount,note '
            '(type = income або expense, date = РРРР-ММ-ДД).'
        ),
    },
    'reports': {
        'title': 'Звіти та підказки',
        'body': (
            'Розділ «Звіти» показує підсумок місяця й порівняння з попереднім.\n'
            '«Підказки» — прості евристики (перевищення бюджетів, динаміка витрат).'
        ),
    },
}


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)


def _parse_month(request) -> date:
    raw = request.GET.get('month') or ''
    today = date.today()
    if len(raw) == 7 and raw[4] == '-':
        try:
            y, m = int(raw[:4]), int(raw[5:7])
            if 1 <= m <= 12:
                return date(y, m, 1)
        except ValueError:
            pass
    return today.replace(day=1)


def _month_stats(user, month_start: date) -> dict:
    start, end = _month_bounds(month_start.year, month_start.month)
    qs = Transaction.objects.filter(
        owner=user,
        occurred_at__gte=start,
        occurred_at__lte=end,
    )
    agg = qs.aggregate(
        income=Sum('amount', filter=Q(tx_type=Transaction.TxType.INCOME)),
        expenses=Sum('amount', filter=Q(tx_type=Transaction.TxType.EXPENSE)),
        count=Count('id'),
    )
    income = agg['income'] or Decimal('0')
    expenses = agg['expenses'] or Decimal('0')
    by_cat = list(
        qs.filter(tx_type=Transaction.TxType.EXPENSE)
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')[:10]
    )
    return {
        'income': income,
        'expenses': expenses,
        'balance': income - expenses,
        'count': agg['count'] or 0,
        'by_category': by_cat,
        'savings_rate': float((income - expenses) / income * 100) if income else 0.0,
    }


@login_required
@require_GET
def reports_home(request):
    month_start = _parse_month(request)
    current = _month_stats(request.user, month_start)
    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    previous = _month_stats(request.user, prev_month)

    # навігація місяців
    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)

    return render(request, 'budgeting/reports.html', {
        'month_start': month_start,
        'month_label': month_start.strftime('%Y-%m'),
        'prev_label': prev_month.strftime('%Y-%m'),
        'next_label': next_month.strftime('%Y-%m'),
        'current': current,
        'previous': previous,
        'expense_delta_pct': _pct_change(previous['expenses'], current['expenses']),
        'income_delta_pct': _pct_change(previous['income'], current['income']),
    })


def _pct_change(old: Decimal, new: Decimal) -> float | None:
    if not old:
        return None
    return float((new - old) / old * 100)


@login_required
@require_GET
def insights(request):
    today = date.today()
    month_start = today.replace(day=1)
    tips: list[dict] = []

    stats = _month_stats(request.user, month_start)
    prev = _month_stats(request.user, (month_start - timedelta(days=1)).replace(day=1))

    if stats['count'] == 0:
        tips.append({
            'level': 'info',
            'title': 'Порожній місяць',
            'text': 'Додайте перші транзакції — з’являться підказки й звіти.',
            'url_name': 'budgeting:transaction_create',
        })

    if stats['expenses'] and prev['expenses']:
        delta = _pct_change(prev['expenses'], stats['expenses'])
        if delta is not None and abs(delta) >= 10:
            direction = 'вищі' if delta > 0 else 'нижчі'
            tips.append({
                'level': 'warning' if delta > 0 else 'success',
                'title': 'Динаміка витрат',
                'text': f'Витрати цього місяця на {abs(delta):.0f}% {direction} за попередній.',
                'url_name': 'budgeting:reports',
            })

    budgets = Budget.objects.filter(
        owner=request.user, month=month_start, is_active=True
    ).select_related('category')
    for b in budgets:
        pct = b.percent
        if pct >= 100:
            tips.append({
                'level': 'danger',
                'title': f'Бюджет «{b.category.name}» вичерпано',
                'text': f'Використано {pct:.0f}% ліміту.',
                'url_name': 'budgeting:budget_detail',
                'url_pk': b.pk,
            })
        elif pct >= 80:
            tips.append({
                'level': 'warning',
                'title': f'Бюджет «{b.category.name}» майже на межі',
                'text': f'Уже {pct:.0f}% від ліміту.',
                'url_name': 'budgeting:budget_detail',
                'url_pk': b.pk,
            })

    goals = SavingsGoal.objects.filter(owner=request.user, is_done=False)
    for g in goals:
        if g.percent >= 100:
            tips.append({
                'level': 'success',
                'title': f'Ціль «{g.title}» досягнута',
                'text': 'Можна відзначити як виконану в картці цілі.',
                'url_name': 'budgeting:goal_detail',
                'url_pk': g.pk,
            })
        elif g.deadline and g.deadline < today and g.percent < 100:
            tips.append({
                'level': 'warning',
                'title': f'Дедлайн цілі «{g.title}» минув',
                'text': f'Прогрес {g.percent:.0f}%.',
                'url_name': 'budgeting:goal_detail',
                'url_pk': g.pk,
            })

    # прогноз до кінця місяця
    day = today.day
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    if day >= 3 and stats['expenses']:
        projected = (stats['expenses'] / day) * days_in_month
        tips.append({
            'level': 'info',
            'title': 'Прогноз витрат місяця',
            'text': (
                f'За поточним темпом до кінця місяця витрати ≈ '
                f'{projected.quantize(Decimal("0.01"))} ₴ '
                f'(зараз {stats["expenses"]} ₴).'
            ),
            'url_name': 'budgeting:reports',
        })

    untagged = Transaction.objects.filter(owner=request.user).annotate(
        n=Count('tags')
    ).filter(n=0).count()
    if untagged >= 5:
        tips.append({
            'level': 'info',
            'title': 'Аудит тегів',
            'text': f'{untagged} транзакцій без тегів — зручно для фільтрації пізніше.',
            'url_name': 'budgeting:transaction_list',
        })

    if not tips:
        tips.append({
            'level': 'success',
            'title': 'Усе спокійно',
            'text': 'Немає критичних сигналів. Продовжуйте вести облік.',
            'url_name': 'budgeting:dashboard',
        })

    return render(request, 'budgeting/insights.html', {'tips': tips})


@login_required
@require_GET
def transaction_calendar(request):
    month_start = _parse_month(request)
    start, end = _month_bounds(month_start.year, month_start.month)
    txs = (
        Transaction.objects.filter(
            owner=request.user,
            occurred_at__gte=start,
            occurred_at__lte=end,
        )
        .values('occurred_at')
        .annotate(
            income=Sum('amount', filter=Q(tx_type=Transaction.TxType.INCOME)),
            expenses=Sum('amount', filter=Q(tx_type=Transaction.TxType.EXPENSE)),
            count=Count('id'),
        )
    )
    by_day = {
        row['occurred_at']: {
            'income': row['income'] or Decimal('0'),
            'expenses': row['expenses'] or Decimal('0'),
            'count': row['count'],
        }
        for row in txs
    }

    cal = calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(month_start.year, month_start.month):
        row = []
        for d in week:
            info = by_day.get(d)
            row.append({
                'date': d,
                'in_month': d.month == month_start.month,
                'info': info,
            })
        weeks.append(row)

    if month_start.month == 12:
        next_month = date(month_start.year + 1, 1, 1)
    else:
        next_month = date(month_start.year, month_start.month + 1, 1)
    prev_month = (month_start - timedelta(days=1)).replace(day=1)

    return render(request, 'budgeting/transaction_calendar.html', {
        'month_start': month_start,
        'month_label': month_start.strftime('%Y-%m'),
        'prev_label': prev_month.strftime('%Y-%m'),
        'next_label': next_month.strftime('%Y-%m'),
        'weeks': weeks,
        'weekday_names': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
    })


@login_required
@require_GET
def help_index(request):
    articles = [
        {'slug': slug, 'title': meta['title']}
        for slug, meta in HELP_ARTICLES.items()
    ]
    return render(request, 'budgeting/help_index.html', {'articles': articles})


@login_required
@require_GET
def help_article(request, slug: str):
    meta = HELP_ARTICLES.get(slug)
    if meta is None:
        messages.warning(request, 'Статтю не знайдено.')
        return redirect('budgeting:help_index')
    return render(request, 'budgeting/help_article.html', {
        'slug': slug,
        'title': meta['title'],
        'body': meta['body'],
        'articles': [
            {'slug': s, 'title': m['title']} for s, m in HELP_ARTICLES.items()
        ],
    })


@login_required
@require_GET
def export_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="finance_helper_transactions.csv"'
    response.write('\ufeff')  # BOM for Excel
    writer = csv.writer(response)
    writer.writerow(['date', 'type', 'category', 'amount', 'note'])
    qs = (
        Transaction.objects.filter(owner=request.user)
        .select_related('category')
        .order_by('occurred_at', 'id')
    )
    for t in qs:
        writer.writerow([
            t.occurred_at.isoformat(),
            t.tx_type,
            t.category.name,
            str(t.amount),
            t.note.replace('\n', ' ').strip(),
        ])
    return response


@login_required
@require_http_methods(['POST'])
def import_csv(request):
    upload = request.FILES.get('csv_file')
    if not upload:
        messages.error(request, 'Оберіть CSV-файл.')
        return redirect('accounts:settings_data')

    try:
        raw = upload.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        messages.error(request, 'Файл має бути в UTF-8.')
        return redirect('accounts:settings_data')

    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        messages.error(request, 'Порожній CSV.')
        return redirect('accounts:settings_data')

    required = {'date', 'type', 'category', 'amount'}
    fields = {f.strip().lower() for f in reader.fieldnames}
    if not required.issubset(fields):
        messages.error(
            request,
            'Потрібні колонки: date, type, category, amount (опційно note).',
        )
        return redirect('accounts:settings_data')

    created = 0
    errors = 0
    for row in reader:
        try:
            norm = {k.strip().lower(): (v or '').strip() for k, v in row.items() if k}
            tx_type = norm['type'].lower()
            if tx_type not in ('income', 'expense'):
                raise ValueError('bad type')
            amount = Decimal(norm['amount'].replace(',', '.'))
            if amount <= 0:
                raise ValueError('amount')
            occurred = date.fromisoformat(norm['date'])
            cat_name = norm['category'][:100] or 'Інше'
            category, _ = Category.objects.get_or_create(
                owner=request.user,
                name=cat_name,
                category_type=tx_type,
                defaults={'icon': 'tag', 'color': '#ff9800', 'is_active': True},
            )
            Transaction.objects.create(
                owner=request.user,
                category=category,
                amount=amount,
                tx_type=tx_type,
                note=norm.get('note', '')[:500],
                occurred_at=occurred,
            )
            created += 1
        except (ValueError, InvalidOperation, KeyError, TypeError):
            errors += 1

    if created:
        messages.success(request, f'Імпортовано транзакцій: {created}.')
    if errors:
        messages.warning(request, f'Пропущено рядків з помилками: {errors}.')
    if not created and not errors:
        messages.info(request, 'У файлі не було рядків даних.')
    return redirect('budgeting:transaction_list')


def build_onboarding(user) -> dict | None:
    """Кроки старту для дашборду; None якщо приховано або все готово."""
    profile = getattr(user, 'profile', None)
    if profile is None:
        from accounts.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
    if profile.onboarding_dismissed:
        return None

    steps = [
        {
            'key': 'category',
            'title': 'Створити категорію',
            'done': Category.objects.filter(owner=user).exists(),
            'url_name': 'budgeting:category_create',
        },
        {
            'key': 'transaction',
            'title': 'Додати транзакцію',
            'done': Transaction.objects.filter(owner=user).exists(),
            'url_name': 'budgeting:transaction_create',
        },
        {
            'key': 'budget',
            'title': 'Задати бюджет',
            'done': Budget.objects.filter(owner=user).exists(),
            'url_name': 'budgeting:budget_create',
        },
        {
            'key': 'goal',
            'title': 'Створити ціль',
            'done': SavingsGoal.objects.filter(owner=user).exists(),
            'url_name': 'budgeting:goal_create',
        },
    ]
    if all(s['done'] for s in steps):
        return None
    done_count = sum(1 for s in steps if s['done'])
    return {'steps': steps, 'done_count': done_count, 'total': len(steps)}
