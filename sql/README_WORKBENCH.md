# MySQL Workbench — кроки для BudgetFlow (розділ 1.2)

СУБД: **MySQL Server 8.0** · клієнт: **MySQL Workbench 8.0**

Так, «схожі на блок-схеми» зв’язки в Workbench — це **ER-діаграма** (таблиці + лінії Foreign Key), не flowchart алгоритму. Саме її треба для п. 1.2.

## A. База даних

1. Відкрийте Workbench → connection **Local instance MySQL80**.
2. File → Open SQL Script → `sql/01_create_database.sql` → Execute (блискавка).
3. У панелі SCHEMAS натисніть refresh — має з’явитись `budgetflow_db`.
4. **Скрін** для звіту: список schemas / нова БД.

## B. Облікові дані Django

У корені проєкту скопіюйте `.env.example` → `.env` і вкажіть пароль root (або окремого користувача):

```
DB_NAME=budgetflow_db
DB_USER=root
DB_PASSWORD=ВАШ_ПАРОЛЬ
DB_HOST=127.0.0.1
DB_PORT=3306
```

Далі в терміналі:

```bash
.\venv\Scripts\activate
python manage.py migrate
python manage.py seed_demo
python manage.py sqlmigrate budgeting 0001 > sql/02_schema_from_django.sql
```

(Останню команду — щоб у звіті був точний SQL від Django.)

## C. ERD (діаграма зв’язків)

1. Меню **Database → Reverse Engineer…**
2. Обрати connection → Next → схему `budgetflow_db`.
3. Відмітити таблиці: `budgeting_*`, `auth_user` (для зв’язку owner).
4. Execute → Finish.
5. Розкласти сутності, зберегти модель: File → Save Model As… → `sql/erd_budgetflow.mwb`.
6. **Скрін ERD** → «Рис. 1.X — ER-діаграма предметної області».

На діаграмі видно: Category 1—N Transaction, Category 1—N Budget, Tag M—N Transaction, усі доменні таблиці → User (owner).

## D. Перевірочні запити

1. File → Open SQL Script → `sql/03_demo_queries.sql`.
2. Виконати по черзі; зробити скріни Result Grid.

## E. Що вставити в Word (1.2)

- Назва і версія СУБД (MySQL 8.0.x).
- ERD + короткий опис сутностей і кардинальності.
- Лістинг `CREATE DATABASE` / фрагмент `CREATE TABLE` (з `02_…sql` або sqlmigrate).
- 1–2 SELECT з JOIN/GROUP BY і скрін результату.
