-- Перевірочні SELECT для скрінів MySQL Workbench (розділ 1.2 / 1.4)
USE finance_helper_db;

-- 1. Транзакції користувача з назвою категорії
SELECT t.id, t.occurred_at, c.name AS category, t.tx_type, t.amount, t.note
FROM budgeting_transaction AS t
JOIN budgeting_category AS c ON c.id = t.category_id
JOIN auth_user AS u ON u.id = t.owner_id
WHERE u.username = 'demo'
ORDER BY t.occurred_at DESC
LIMIT 20;

-- 2. Сума витрат по категоріях за поточний місяць
SELECT c.name, SUM(t.amount) AS total_expense, COUNT(*) AS cnt
FROM budgeting_transaction AS t
JOIN budgeting_category AS c ON c.id = t.category_id
WHERE t.tx_type = 'expense'
  AND YEAR(t.occurred_at) = YEAR(CURDATE())
  AND MONTH(t.occurred_at) = MONTH(CURDATE())
GROUP BY c.name
ORDER BY total_expense DESC;

-- 3. Бюджет vs факт
SELECT
  c.name,
  b.amount AS budget_limit,
  COALESCE(SUM(t.amount), 0) AS spent,
  b.amount - COALESCE(SUM(t.amount), 0) AS remaining
FROM budgeting_budget AS b
JOIN budgeting_category AS c ON c.id = b.category_id
LEFT JOIN budgeting_transaction AS t
  ON t.category_id = b.category_id
 AND t.owner_id = b.owner_id
 AND t.tx_type = 'expense'
 AND YEAR(t.occurred_at) = YEAR(b.month)
 AND MONTH(t.occurred_at) = MONTH(b.month)
GROUP BY c.name, b.amount
ORDER BY c.name;

-- 4. Прогрес цілей накопичення
SELECT title, target_amount, saved_amount,
       ROUND(saved_amount / target_amount * 100, 1) AS percent_done,
       is_done
FROM budgeting_savingsgoal
ORDER BY is_done, title;
