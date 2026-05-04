CREATE DATABASE IF NOT EXISTS `bookms` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `bookms`;

CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键ID',
  `username` VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希值',
  `role` ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER' COMMENT '角色：管理员/普通用户',
  `real_name` VARCHAR(64) NULL COMMENT '真实姓名',
  `phone` VARCHAR(20) NULL COMMENT '手机号',
  `email` VARCHAR(128) NULL COMMENT '邮箱',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT='用户表';

CREATE TABLE IF NOT EXISTS `books` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '图书主键ID',
  `isbn` VARCHAR(32) UNIQUE NULL COMMENT 'ISBN编号',
  `title` VARCHAR(255) NOT NULL COMMENT '书名',
  `author` VARCHAR(128) NOT NULL COMMENT '作者',
  `category` VARCHAR(64) NULL COMMENT '分类',
  `publisher` VARCHAR(128) NULL COMMENT '出版社',
  `publish_date` DATE NULL COMMENT '出版日期',
  `total_stock` INT NOT NULL DEFAULT 0 COMMENT '总库存',
  `available_stock` INT NOT NULL DEFAULT 0 COMMENT '可借库存',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：1上架，0下架',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT='图书表';

CREATE TABLE IF NOT EXISTS `borrow_records` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '借阅记录主键ID',
  `user_id` BIGINT NOT NULL COMMENT '借阅用户ID',
  `book_id` BIGINT NOT NULL COMMENT '图书ID',
  `borrowed_at` DATETIME NOT NULL COMMENT '借出时间',
  `due_at` DATETIME NOT NULL COMMENT '应还时间',
  `returned_at` DATETIME NULL COMMENT '实际归还时间',
  `status` ENUM('BORROWED', 'OVERDUE', 'RETURNED') NOT NULL DEFAULT 'BORROWED' COMMENT '状态：借阅中/逾期/已归还',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT `fk_borrow_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_borrow_book` FOREIGN KEY (`book_id`) REFERENCES `books`(`id`)
) COMMENT='借阅记录表';

CREATE TABLE IF NOT EXISTS `reservations` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '预约记录主键ID',
  `user_id` BIGINT NOT NULL COMMENT '预约用户ID',
  `book_id` BIGINT NOT NULL COMMENT '图书ID',
  `status` ENUM('ACTIVE', 'CANCELLED', 'FULFILLED', 'EXPIRED') NOT NULL DEFAULT 'ACTIVE' COMMENT '状态：预约中/已取消/已完成/已失效',
  `reserved_at` DATETIME NOT NULL COMMENT '预约时间',
  `expired_at` DATETIME NULL COMMENT '失效时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  CONSTRAINT `fk_reservation_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  CONSTRAINT `fk_reservation_book` FOREIGN KEY (`book_id`) REFERENCES `books`(`id`)
) COMMENT='预约记录表';

-- =========================
-- 初始化演示数据（可按需删除）
-- =========================

-- 用户数据：1 个管理员 + 2 个普通用户
-- 演示账号密码（三账号相同）：BookMS@demo123（Werkzeug scrypt 哈希，与后端 check_password_hash 一致）
INSERT INTO `users` (`id`, `username`, `password_hash`, `role`, `real_name`, `phone`, `email`, `status`)
VALUES
  (1, 'admin', 'scrypt:32768:8:1$71J9DbeDxftaPKBb$bf868a7f14e1c6090409467a1233918979eafdab211fc554e28855bc22d6e2caf09d410384034af649e67675a0989f372a6697257247dbd6bec93387eab23ec8', 'ADMIN', '系统管理员', '13800000000', 'admin@bookms.local', 1),
  (2, 'user001', 'scrypt:32768:8:1$71J9DbeDxftaPKBb$bf868a7f14e1c6090409467a1233918979eafdab211fc554e28855bc22d6e2caf09d410384034af649e67675a0989f372a6697257247dbd6bec93387eab23ec8', 'USER', '张三', '13800000001', 'user001@bookms.local', 1),
  (3, 'user002', 'scrypt:32768:8:1$71J9DbeDxftaPKBb$bf868a7f14e1c6090409467a1233918979eafdab211fc554e28855bc22d6e2caf09d410384034af649e67675a0989f372a6697257247dbd6bec93387eab23ec8', 'USER', '李四', '13800000002', 'user002@bookms.local', 1)
ON DUPLICATE KEY UPDATE
  `username` = VALUES(`username`),
  `password_hash` = VALUES(`password_hash`),
  `role` = VALUES(`role`),
  `real_name` = VALUES(`real_name`),
  `phone` = VALUES(`phone`),
  `email` = VALUES(`email`),
  `status` = VALUES(`status`);

-- 图书数据
INSERT INTO `books` (`id`, `isbn`, `title`, `author`, `category`, `publisher`, `publish_date`, `total_stock`, `available_stock`, `status`)
VALUES
  (1, '9787111128069', 'Python 核心编程', 'Wesley Chun', '编程', '机械工业出版社', '2020-01-01', 10, 8, 1),
  (2, '9787115428028', 'Flask Web 开发实战', '李辉', 'Web开发', '人民邮电出版社', '2021-06-01', 6, 5, 1),
  (3, '9787302511853', 'Vue.js 设计与实现', '霍春阳', '前端', '清华大学出版社', '2022-03-01', 5, 5, 1)
ON DUPLICATE KEY UPDATE `title` = VALUES(`title`);

-- 借阅记录数据（示例：user001 借走 2 本）
INSERT INTO `borrow_records` (`id`, `user_id`, `book_id`, `borrowed_at`, `due_at`, `returned_at`, `status`)
VALUES
  (1, 2, 1, '2026-04-01 10:00:00', '2026-05-01 10:00:00', NULL, 'BORROWED'),
  (2, 2, 2, '2026-03-01 09:00:00', '2026-03-31 09:00:00', NULL, 'OVERDUE')
ON DUPLICATE KEY UPDATE `status` = VALUES(`status`);

-- 预约记录数据（支持有库存预约）
INSERT INTO `reservations` (`id`, `user_id`, `book_id`, `status`, `reserved_at`, `expired_at`)
VALUES
  (1, 3, 3, 'ACTIVE', '2026-04-15 14:00:00', NULL)
ON DUPLICATE KEY UPDATE `status` = VALUES(`status`);
