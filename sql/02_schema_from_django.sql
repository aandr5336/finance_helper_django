--
-- Create model Category
--
CREATE TABLE `budgeting_category` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `icon` varchar(50) NOT NULL, `color` varchar(7) NOT NULL, `category_type` varchar(10) NOT NULL, `is_active` bool NOT NULL, `created_at` datetime(6) NOT NULL, `owner_id` integer NOT NULL);
--
-- Create model Budget
--
CREATE TABLE `budgeting_budget` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `amount` numeric(12, 2) NOT NULL, `month` date NOT NULL, `is_active` bool NOT NULL, `created_at` datetime(6) NOT NULL, `owner_id` integer NOT NULL, `category_id` bigint NOT NULL);
--
-- Create model SavingsGoal
--
CREATE TABLE `budgeting_savingsgoal` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `title` varchar(150) NOT NULL, `description` longtext NOT NULL, `target_amount` numeric(12, 2) NOT NULL, `saved_amount` numeric(12, 2) NOT NULL, `deadline` date NULL, `is_done` bool NOT NULL, `created_at` datetime(6) NOT NULL, `owner_id` integer NOT NULL);
--
-- Create model Tag
--
CREATE TABLE `budgeting_tag` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(50) NOT NULL, `created_at` datetime(6) NOT NULL, `owner_id` integer NOT NULL);
--
-- Create model Transaction
--
CREATE TABLE `budgeting_transaction` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `amount` numeric(12, 2) NOT NULL, `tx_type` varchar(10) NOT NULL, `note` longtext NOT NULL, `occurred_at` date NOT NULL, `created_at` datetime(6) NOT NULL, `category_id` bigint NOT NULL, `owner_id` integer NOT NULL);
CREATE TABLE `budgeting_transaction_tags` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `transaction_id` bigint NOT NULL, `tag_id` bigint NOT NULL);
--
-- Create constraint uniq_category_owner_name_type on model category
--
ALTER TABLE `budgeting_category` ADD CONSTRAINT `uniq_category_owner_name_type` UNIQUE (`owner_id`, `name`, `category_type`);
--
-- Create constraint uniq_budget_owner_category_month on model budget
--
ALTER TABLE `budgeting_budget` ADD CONSTRAINT `uniq_budget_owner_category_month` UNIQUE (`owner_id`, `category_id`, `month`);
--
-- Create constraint uniq_tag_owner_name on model tag
--
ALTER TABLE `budgeting_tag` ADD CONSTRAINT `uniq_tag_owner_name` UNIQUE (`owner_id`, `name`);
ALTER TABLE `budgeting_category` ADD CONSTRAINT `budgeting_category_owner_id_a1a3510a_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `budgeting_budget` ADD CONSTRAINT `budgeting_budget_owner_id_78f34dad_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `budgeting_budget` ADD CONSTRAINT `budgeting_budget_category_id_1ade866a_fk_budgeting_category_id` FOREIGN KEY (`category_id`) REFERENCES `budgeting_category` (`id`);
ALTER TABLE `budgeting_savingsgoal` ADD CONSTRAINT `budgeting_savingsgoal_owner_id_7a21da80_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `budgeting_tag` ADD CONSTRAINT `budgeting_tag_owner_id_2a895dd7_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `budgeting_transaction` ADD CONSTRAINT `budgeting_transactio_category_id_449c14a5_fk_budgeting` FOREIGN KEY (`category_id`) REFERENCES `budgeting_category` (`id`);
ALTER TABLE `budgeting_transaction` ADD CONSTRAINT `budgeting_transaction_owner_id_2c1b2dad_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `budgeting_transaction_tags` ADD CONSTRAINT `budgeting_transaction_tags_transaction_id_tag_id_8a201393_uniq` UNIQUE (`transaction_id`, `tag_id`);
ALTER TABLE `budgeting_transaction_tags` ADD CONSTRAINT `budgeting_transactio_transaction_id_127a76f7_fk_budgeting` FOREIGN KEY (`transaction_id`) REFERENCES `budgeting_transaction` (`id`);
ALTER TABLE `budgeting_transaction_tags` ADD CONSTRAINT `budgeting_transaction_tags_tag_id_a643819b_fk_budgeting_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `budgeting_tag` (`id`);
