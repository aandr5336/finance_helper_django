# 1.3. Опис програмної реалізації

## Структура проєкту

- `budget_project/` — settings, urls, wsgi; PyMySQL як MySQLdb.
- `budgeting/` — домен (моделі, views, forms, templatetags, seed).
- `accounts/` — реєстрація, auth views, `LastActivityMiddleware`.
- `templates/`, `static/css/custom.css`, `sql/`, `docs/`.

Ключові налаштування: `INSTALLED_APPS` (+ debug_toolbar, budgeting, accounts); `DATABASES` → MySQL з `.env`; `LOGIN_URL = accounts:login`; `STATICFILES_DIRS`; `LANGUAGE_CODE = uk`.

## Моделі

| Модель | Поля / зв’язки | Meta / методи |
|--------|----------------|---------------|
| Category | owner FK CASCADE, name, icon, color, category_type choices, is_active, created_at | UniqueConstraint; `__str__`, `get_absolute_url` |
| Transaction | owner CASCADE, category PROTECT, amount, tx_type, note, occurred_at, tags M2M | permissions `can_view_all_transactions`; `clean()` |
| Budget | owner, category CASCADE, amount, month, is_active | UniqueConstraint; `spent`/`percent` |
| SavingsGoal | owner, title, description, target/saved, deadline, is_done | `percent`, `remaining` |
| Tag | owner, name | UniqueConstraint; M2M related_name=`transactions` |

Data-міграція `0002_create_roles.py` (RunPython): групи `users` / `analysts` + permission.

## Форми

- `TransactionForm`, `CategoryForm`, `BudgetForm`, `SavingsGoalForm` — ModelForm, явний `fields`, без `owner`.
- `TransactionFilterForm` — звичайний `forms.Form`.
- `validate_positive_amount` + `clean_occurred_at` / `clean()`; повідомлення українською.
- CSRF + PRG у Create/Update/Delete та `goal_deposit`.

## Представлення

| Клас / функція | URL name | Що перевизначено |
|----------------|----------|------------------|
| `dashboard` (FBV) | `budgeting:dashboard` | aggregate/annotate статистика |
| `TransactionListView` | `transaction_list` | `get_queryset` (Q-фільтр), `get_context_data`, paginate_by=10 |
| `TransactionDetailView` | `transaction_detail` | select_related / prefetch |
| `TransactionCreateView` | `transaction_create` | `form_valid` → owner |
| `TransactionUpdateView` | `transaction_update` | OwnerEditMixin + form_valid |
| `TransactionDeleteView` | `transaction_delete` | лише власник |
| Category/Budget/Goal List+Detail (+CRUD) | `category_*`, `budget_*`, `goal_*` | queryset по owner |
| `goal_deposit` (FBV POST) | `goal_deposit` | поповнення цілі |
| `system_overview` | `system_overview` | `@permission_required` |

Чому FBV для дашборду: кілька незалежних агрегатів без стану форми; CRUD — стандартні Generic Views.

## Маршрути (фрагмент)

Усі з `app_name`: `budgeting`, `accounts`. У шаблонах `{% url %}`, у коді `reverse` / `reverse_lazy`. Конвертер `<int:pk>`.

## Шаблони

`base.html` ← extends; includes: `navbar`, `messages`, `pagination`; inclusion_tag `budget_progress_bar`; simple_tag `uah`. Bootstrap 5 + `custom.css`.

## Ролі

| Роль | Може | Де перевірка |
|------|------|--------------|
| anonymous | login/register | — |
| users | CRUD своїх даних | LoginRequiredMixin, OwnerEditMixin, filter owner |
| analysts | + огляд системи | `permission_required('budgeting.can_view_all_transactions')` |

## Оптимізація

На списках: `select_related('category','owner')`, `prefetch_related('tags')`. Перевірка кількості запитів — Django Debug Toolbar (`/__debug__/` при DEBUG).
