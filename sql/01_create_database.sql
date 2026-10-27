-- MySQL 8.x — створення схеми для Finance Helper
-- Виконати в MySQL Workbench: File → Open SQL Script → Execute

CREATE DATABASE IF NOT EXISTS finance_helper_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- За потреби (локальна розробка):
-- CREATE USER IF NOT EXISTS 'finance_helper'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON finance_helper_db.* TO 'finance_helper'@'localhost';
-- FLUSH PRIVILEGES;

USE finance_helper_db;
