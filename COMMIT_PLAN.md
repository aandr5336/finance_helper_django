# План ~15 логічних комітів (історія практики)

Код на диску вже є. Історію git скинуто. Коли пишеш номер кроку (наприклад `коміт 3`), я:
1. додаю/залишаю в індексі **лише файли цього кроку**;
2. роблю один коміт із відповідним повідомленням;
3. решту файлів не чіпаю в цьому коміті.

Так дати комітів будуть різні (коли ти напишеш), а не всі «в одну секунду».

---

## Коли писати (орієнтовний графік)

Інтервал **1–2 дні** між кроками. Підстав свої дати.

| # | Коли писати (приклад) | Що написати мені | Зміст коміту |
|---|------------------------|------------------|--------------|
| 1 | День 1, ранок | `коміт 1` | Scaffold: `manage.py`, `budget_project/`, `requirements.txt`, `.gitignore`, `.env.example` |
| 2 | День 1, вечір | `коміт 2` | MySQL settings + `python-dotenv`/`django-environ`, PyMySQL |
| 3 | День 2 | `коміт 3` | Apps `budgeting`, `accounts` (порожні apps) |
| 4 | День 3 | `коміт 4` | Моделі `Category`, `Tag`, `Transaction`, `Budget`, `SavingsGoal` |
| 5 | День 4 | `коміт 5` | Міграції + data-міграція ролей + admin |
| 6 | День 5 | `коміт 6` | Auth: реєстрація, login/logout, password |
| 7 | День 6 | `коміт 7` | Forms + validators |
| 8 | День 7 | `коміт 8` | Transaction CRUD (CBV) + urls |
| 9 | День 8 | `коміт 9` | Category / Budget / Goal views |
| 10 | День 9 | `коміт 10` | Dashboard FBV + analytics (Q/annotate) + roles overview |
| 11 | День 10 | `коміт 11` | Шаблони base/navbar + списки/форми (базовий UI) |
| 12 | День 11 | `коміт 12` | Темна тема Flet-палітра (`custom.css`) + прогрес-бари |
| 13 | День 12 | `коміт 13` | `sql/` Workbench скрипти + README_WORKBENCH |
| 14 | День 13 | `коміт 14` | `docs/REPORT_1_*` + головний README |
| 15 | День 14 | `коміт 15` | seed_demo + smoke_test + дрібні фікси безпеки/N+1 |

Можна стиснути до **через день** (два тижні → ~тиждень) або розтягнути на всю практику.

---

## Правила для тебе

1. Пиши рівно: **`коміт N`** (або `зроби коміт N`).
2. Не проси «закоміть усе зараз» — зіб’є план.
3. Між комітами можна користуватись застосунком локально; у git потрапляє лише те, що додамо на кроці.
4. Push на GitHub — окремо, коли скажеш (краще після кількох комітів).

---

## Приклад повідомлень комітів

1. `Scaffold Django project structure and dependencies.`
2. `Configure MySQL database settings from environment.`
3. `Create budgeting and accounts apps.`
4. `Add domain models for categories, transactions, budgets and goals.`
5. `Add migrations, role data migration and admin registration.`
6. `Implement user registration, login and password flows.`
7. `Add ModelForms, filter form and Ukrainian validators.`
8. `Implement transaction CRUD with generic class-based views.`
9. `Add category, budget and savings goal views.`
10. `Add dashboard analytics and privileged system overview.`
11. `Add shared templates and page markup.`
12. `Apply Finance Helper dark theme and fix progress bars.`
13. `Add MySQL Workbench SQL scripts and ERD instructions.`
14. `Add report section drafts and project README.`
15. `Add demo seed command and smoke checks.`
