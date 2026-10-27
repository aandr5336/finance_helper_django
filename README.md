# Finance Helper — Django + MySQL

Система автоматизації бюджетування та аналізу ефективності витрат користувача.

- **Framework:** Django 5.2  
- **СУБД:** MySQL 8.0 (НЕ SQLite)  
- **Клієнт БД для звіту:** MySQL Workbench 8.0  

## Швидкий старт

### 1. MySQL Workbench

1. Створіть БД скриптом [`sql/01_create_database.sql`](sql/01_create_database.sql).
2. Детальна інструкція ERD і SELECT: [`sql/README_WORKBENCH.md`](sql/README_WORKBENCH.md).

### 2. Python-оточення

```powershell
cd C:\Users\Acer\Desktop\ZVIT_3\DJANGO_PROJECT
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Відредагуйте `.env`: вкажіть `SECRET_KEY` (довгий випадковий рядок) і `DB_PASSWORD` (пароль root MySQL).

### 3. Міграції та демо-дані

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser   # опційно
python manage.py runserver
```

Відкрийте http://127.0.0.1:8000/

**Демо-акаунти після `seed_demo`:**

| Логін    | Пароль         | Роль              |
|----------|----------------|-------------------|
| demo     | demo12345      | звичайний user    |
| analyst  | analyst12345   | analyst (огляд)   |

## Змінні оточення

Див. `.env.example`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Структура

- `budgeting/` — моделі, CRUD, аналітика  
- `accounts/` — реєстрація, вхід/вихід, пароль, middleware  
- `sql/` — скрипти та інструкція Workbench  
- `docs/` — заготовки тексту для розділу 1 звіту  

## Звіт

Матеріали: `docs/REPORT_1_1.md` … `REPORT_1_4.md`, `REPORT_1_CONCLUSION.md`.

