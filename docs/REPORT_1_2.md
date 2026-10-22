# 1.2. Проєктування бази даних

## СУБД

- **MySQL Server 8.0** (локальний екземпляр MySQL80).
- Клієнт моделювання та запитів: **MySQL Workbench 8.0**.
- Charset: `utf8mb4`, collation: `utf8mb4_unicode_ci`.
- Схема: `budgetflow_db` (`sql/01_create_database.sql`).

Покрокова робота в Workbench: `sql/README_WORKBENCH.md`.

## ERD

Після `migrate` виконати **Database → Reverse Engineer…** і зберегти модель у `sql/erd_budgetflow.mwb`.

**Рис. 1.1 — ER-діаграма** (скрін з Workbench): прямокутники = таблиці, лінії = Foreign Key.

### Сутності та зв’язки

| Сутність | Призначення | Ключові поля | Зв’язки |
|----------|-------------|--------------|---------|
| auth_user | Користувач Django | id, username | 1—N до всіх доменних через owner |
| budgeting_category | Категорія доходу/витрати | name, category_type, is_active | owner N:1 User; 1:N Transaction, Budget |
| budgeting_transaction | Фінансова операція | amount, tx_type, occurred_at | N:1 Category (PROTECT); M:N Tag |
| budgeting_tag | Мітка транзакції | name | M:N Transaction через `budgeting_transaction_tags` |
| budgeting_budget | Місячний ліміт | amount, month | N:1 Category |
| budgeting_savingsgoal | Ціль накопичення | target_amount, saved_amount, is_done | N:1 User |

Кардинальність: один користувач — багато категорій/транзакцій; одна категорія — багато транзакцій; теги — Many-to-Many.

## SQL-скрипти

1. `sql/01_create_database.sql` — створення БД.
2. `sql/02_schema_from_django.sql` — CREATE TABLE (діалект MySQL); після migrate оновити через `sqlmigrate`.
3. `sql/03_demo_queries.sql` — SELECT з JOIN / GROUP BY для демонстрації.

**Рис. 1.2** — список таблиць у SCHEMAS.  
**Рис. 1.3** — Result Grid одного з SELECT.

### Фрагмент (створення БД)

```sql
CREATE DATABASE IF NOT EXISTS budgetflow_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### Фрагмент (агрегація витрат)

```sql
SELECT c.name, SUM(t.amount) AS total_expense
FROM budgeting_transaction AS t
JOIN budgeting_category AS c ON c.id = t.category_id
WHERE t.tx_type = 'expense'
GROUP BY c.name;
```

Моделі Django в п. 1.3 відповідають цим таблицям один-до-одного.
