-- MySQL 8.x — створення схеми для BudgetFlow
-- Виконати в MySQL Workbench: File → Open SQL Script → Execute

CREATE DATABASE IF NOT EXISTS budgetflow_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- За потреби (локальна розробка):
-- CREATE USER IF NOT EXISTS 'budgetflow'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON budgetflow_db.* TO 'budgetflow'@'localhost';
-- FLUSH PRIVILEGES;

USE budgetflow_db;
