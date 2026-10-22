# Промпт для створення Django-застосунку + матеріали до звіту

Скопіюй блок між лініями `---` і встав у новий чат Cursor у папці `DJANGO_PROJECT`.

---

## РОЛЬ

Ти — досвідчений Django-розробник і помічник зі звіту з практики. Створи з нуля повний робочий вебзастосунок Django (український UI) і підготуй артефакти для **Розділу 1** звіту (БД у MySQL Workbench + опис реалізації). Не пиши пусту теорію Django — реалізуй код під **кожну** обов’язкову вимогу (В1–В8) і бажано Д1–Д7. Зроби кілька логічних git-комітів протягом роботи (не один наприкінці).

## КОНТЕКСТ ЗВІТУ (навіщо це все)

Це звіт з практики: тема одна на два різні стеки. **Цей проєкт = Розділ 1** («Розробка вебсайту та робота з базою даних» на Django + MySQL). Другий застосунок (Payload/TS) — окремий розділ, тут його не роби.

Структура Розділу 1, під яку треба підготувати матеріали:

| Підрозділ | Що зробити в коді / артефактах |
|-----------|--------------------------------|
| **1.1** Аналіз предметної області | Текст у `docs/REPORT_1_1.md`: опис області, цілі, користувачі, функції, обмеження |
| **1.2** Проєктування БД | ERD + SQL-скрипти з **MySQL Workbench** (діалект MySQL); інструкція нижче |
| **1.3** Опис програмної реалізації | `docs/REPORT_1_3.md`: класи/функції Django, таблиці views/URL/ролей |
| **1.4** Контрольний приклад | `docs/REPORT_1_4.md`: типовий сценарій крок за кроком (місця під скріни) |
| Висновок до розд. 1 | Короткий абзац у `docs/REPORT_1_CONCLUSION.md` |

Узгодженість: моделі в 1.2 і 1.3 збігаються; SQL у 1.2 — **діалект MySQL** (зручно з `sqlmigrate` + Workbench); сценарій 1.4 проходить тими сторінками, що описані в 1.3.

## ТЕМА ЗАСТОСУНКУ

**Система автоматизації процесів бюджетування та аналізу ефективності витрат користувача** (BudgetFlow).

Аналог попереднього Flet Finance Helper, але як Django web-app з **MySQL**.

### Функції для користувача
1. Реєстрація / вхід / вихід (logout лише POST).
2. Категорії доходів і витрат.
3. Транзакції (сума, дата, примітка, категорія, тип).
4. Місячні бюджети по категоріях + прогрес / перевитрата.
5. Фінансові цілі (накопичення).
6. Дашборд і аналітика ефективності витрат (баланс, savings rate, топ категорій, фільтри).
7. Привілейована роль (analyst/staff) — окрема захищена сторінка огляду системи.

UI, валідація, `verbose_name` — **українською**.

## СТЕК (В1, В2) — MYSQL, НЕ SQLITE

- Python 3.11+, Django 5.x, версії зафіксовані в `requirements.txt`.
- `venv`.
- СУБД: **MySQL 8.x** через драйвер `mysqlclient` (або `PyMySQL` з ініціалізацією, якщо mysqlclient важко поставити на Windows — задокументуй вибір у README).
- У README і звіті явно: **MySQL 8.x + MySQL Workbench**.
- Секрети лише з `.env` (`django-environ` або `python-dotenv`): `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
- `.env` у `.gitignore`; у репо — `.env.example` без значень.
- `README.md`: встановлення MySQL, створення БД у Workbench, venv, migrate, seed, runserver.
- Структура:
  ```
  budget_project/
  budgeting/          # app_name = 'budgeting'
  accounts/           # auth / ролі
  templates/
  static/
  sql/                # експортовані SQL + інструкції Workbench
  docs/               # заготовки розділу 1 звіту
  manage.py
  requirements.txt
  .env.example
  README.md
  ```
- URL: `app_name` + імена; у шаблонах `{% url %}`, у коді `reverse()` / `reverse_lazy()`. Без хардкод-шляхів.

### Приклад DATABASES (орієнтир)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="127.0.0.1"),
        "PORT": env("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}
```

## MYSQL WORKBENCH — ОБОВ’ЯЗКОВИЙ БЛОК ДЛЯ РОЗДІЛУ 1.2

Окрім Django-міграцій, підготуй у репозиторії папку `sql/` і файл `docs/REPORT_1_2.md` з покроковою інструкцією **що саме робити в MySQL Workbench** (щоб студент міг повторити і вставити скріни у Word).

### Крок A. Підключення і створення схеми
1. Відкрити **MySQL Workbench** → Local instance.
2. Створити схему (schema/database), напр. `budgetflow_db`, charset **utf8mb4**, collation **utf8mb4_unicode_ci**.
3. Створити окремого користувача (або використати root для локалки) і права на цю БД.
4. Заповнити `.env` тими ж `DB_*`.
5. Зробити скрін: список schemas / нова БД (для рис. у 1.2).

SQL для звіту (збережи як `sql/01_create_database.sql`):

```sql
CREATE DATABASE IF NOT EXISTS budgetflow_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### Крок B. Таблиці через Django, але SQL — у діалекті MySQL
1. `python manage.py makemigrations`
2. `python manage.py sqlmigrate budgeting 0001` (і наступні) → зберегти вивід у `sql/02_schema_from_django.sql` (**це діалект MySQL** — саме його цитувати в 1.2).
3. `python manage.py migrate`
4. У Workbench: refresh schemas → розгорнути tables → скрін списку таблиць.

### Крок C. ERD у Workbench (обов’язково для 1.2)
1. Menu: **Database → Reverse Engineer…**
2. Вибрати connection → схему `budgetflow_db`.
3. Імпортувати таблиці домену: щонайменше  
   `budgeting_category`, `budgeting_transaction`, `budgeting_budget`, `budgeting_savingsgoal`, `budgeting_tag`, M2M `budgeting_transaction_tags`, плюс за потреби `auth_user` (або показати зв’язок owner → user).
4. Розкласти сутності, підписати зв’язки (1:N, M:N).
5. Зберегти модель: `sql/erd_budgetflow.mwb`
6. Експорт зображення ERD (File → Export / Print to PDF або скрін) — шлях описати в `docs/REPORT_1_2.md` як «Рис. 1.X — ER-діаграма».
7. У `docs/REPORT_1_2.md` коротко описати кожну сутність: призначення, ключові атрибути, PK/FK, кардинальність.

### Крок D. Демо-дані і перевірочні SELECT (для скрінів Workbench)
1. `python manage.py seed_demo` (або data-міграція).
2. У Workbench SQL Editor виконати і зберегти скрипти в `sql/03_demo_queries.sql`, наприклад:
   - транзакції користувача з назвою категорії (JOIN);
   - сума витрат по категоріях за місяць (`GROUP BY`);
   - порівняння бюджету і фактичних витрат;
   - прогрес цілей накопичення.
3. Скріни Result Grid — для 1.2 / 1.4.

### Крок E. Що покласти в репозиторій
```
sql/
  01_create_database.sql
  02_schema_from_django.sql      # з sqlmigrate, діалект MySQL
  03_demo_queries.sql
  README_WORKBENCH.md            # короткі кроки A–D українською
  erd_budgetflow.mwb             # якщо вдалося зберегти
docs/
  REPORT_1_1.md … REPORT_1_4.md
  REPORT_1_CONCLUSION.md
```

У `README.md` проєкту дай посилання на `sql/README_WORKBENCH.md`.

**Важливо:** у розділі 1.2 звіту описуй **свою** БД (таблиці BudgetFlow), а не теорію нормалізації. SQL-лістинги — MySQL, узгоджені з моделями Django.

## МОДЕЛІ (В3 + Д1–Д3, Д6)

≥4 власні моделі (User не рахується), `owner = ForeignKey(User)`, різні типи полів, `__str__()`, міграції + **одна data-міграція RunPython**, реєстрація в admin (`list_display`, `search_fields`/`list_filter`), seed для демо.

### Схема
1. **Category** — name, icon, color, category_type (expense/income), is_active, created_at; UniqueConstraint(owner, name, category_type); `get_absolute_url`
2. **Transaction** — **повний CRUD**; category FK (`PROTECT` або `SET_NULL`), amount, tx_type, note, occurred_at; Meta.permissions; `get_absolute_url`
3. **Budget** — category, amount, month, is_active; UniqueConstraint(owner, category, month)
4. **SavingsGoal** — title, description, target_amount, saved_amount, deadline, is_done
5. **Tag** + `Transaction.tags` M2M з `related_name='transactions'` (Д1)

Для кожного FK обґрунтуй `on_delete` (Д2). Meta: ordering, verbose_name, UniqueConstraint (Д3).

## ШАБЛОНИ / СТАТИКА / ФОРМИ / VIEWS / РОЛІ / БЕЗПЕКА

Виконай повністю вимоги практики:

- **В4:** base.html + extends/include; Bootstrap + власний CSS; ≥1 custom DTL tag.
- **В5:** ModelForm з явним `fields` без owner; ≥1 forms.Form; валідатор + clean_*; csrf; PRG.
- **В6:** CRUD Transaction на List/Detail/Create/Update/DeleteView; для інших — List+Detail; ≥1 FBV; paginate_by; get_absolute_url; override get_queryset/get_context_data/form_valid; `<int:pk>`.
- **В7:** реєстрація, login, logout POST; owner у form_valid; LoginRequiredMixin; свої записи лише свої; ≥2 ролі + серверна перевірка привілеїв.
- **В8:** без небезпечного raw SQL; без |safe на юзер-контенті.
- **Д4–Д5:** Q-фільтри, annotate/aggregate, select_related/prefetch_related, Debug Toolbar.
- **Д6–Д7 (бажано):** Meta.permissions + groups; password change/reset; простий middleware.

## GIT (В1.2)

Кілька комітів, напр.: scaffold+MySQL settings → models/migrations → auth/roles → CRUD → analytics/UI → sql/docs/seed/README.

## ДОКУМЕНТАЦІЯ ЗВІТУ (згенеруй файли)

### `docs/REPORT_1_1.md`
Опис предметної області, цілі/завдання, користувачі (звичайний / аналітик), функції, обмеження (один власник бачить свої дані, валідація сум тощо).

### `docs/REPORT_1_2.md`
- Яка СУБД і версія (MySQL 8 + Workbench).
- Опис сутностей і зв’язків (як на ERD).
- Посилання на `sql/*.sql` і кроки Reverse Engineer.
- 2–4 ключові SQL-фрагменти (CREATE / SELECT з JOIN) з поясненням українською.
- Місця під підписи рисунків: «Рис. 1.1 — ERD», «Рис. 1.2 — список таблиць у Workbench», «Рис. 1.3 — результат SELECT…».

### `docs/REPORT_1_3.md`
- Структура проєкту, INSTALLED_APPS, DATABASES, LOGIN_URL, static, env.
- Моделі = як у 1.2.
- Форми і рівні валідації.
- Таблиця: клас/функція → URL name → що перевизначено і навіщо.
- Таблиця маршрутів.
- Дерево шаблонів + custom tag.
- Таблиця: роль → що може → де перевірка в коді.
- Якщо є Д5: до/після кількості запитів (Debug Toolbar).

### `docs/REPORT_1_4.md`
Типовий сценарій (8–12 кроків) зі місцями під скріни, напр.:
реєстрація → логін → категорія → транзакція → бюджет → ціль → фільтр → аналітика → (роль analyst) огляд → перевірка того ж у Workbench SELECT.
Сценарій має збігатися зі сторінками з 1.3.

### `docs/REPORT_1_CONCLUSION.md`
5–8 речень: що реалізовано, роль MySQL/Workbench, готовність до розділу тестування.

## КРИТЕРІЙ ГОТОВНОСТІ

- [ ] В1–В8 виконані  
- [ ] MySQL (не SQLite), `.env` / `.env.example`  
- [ ] `sql/` + інструкція Workbench (create DB, migrate, Reverse Engineer ERD, demo SELECT)  
- [ ] `docs/REPORT_1_1` … `1_4` + висновок  
- [ ] seed_demo + README  
- [ ] кілька git-комітів  

## ПОРЯДОК РОБОТИ

1. venv, requirements (`Django`, `mysqlclient`/`PyMySQL`, `django-environ`, `django-debug-toolbar`), проєкт, apps, gitignore, env.  
2. Інструкція Workbench: створити `budgetflow_db` → заповнити `.env`.  
3. Моделі → makemigrations → зберегти `sqlmigrate` у `sql/` → migrate → data-migration → admin.  
4. Auth, групи, permissions.  
5. Forms, CBV CRUD, FBV dashboard, шаблони, static, templatetag.  
6. Q/annotate, select_related, Debug Toolbar.  
7. seed_demo; demo SQL у Workbench.  
8. Reverse Engineer ERD; заповнити `docs/REPORT_1_*.md` і `sql/README_WORKBENCH.md`.  
9. Кілька комітів.  
10. Перевірити `runserver` проти MySQL.

Починай реалізацію зараз у поточній директорії. Якщо MySQL ще не встановлений — все одно напиши код і `sql/` + чіткі кроки Workbench; не перемикай ENGINE на SQLite.

---
