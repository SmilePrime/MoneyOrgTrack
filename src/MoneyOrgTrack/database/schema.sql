-- Схема базы данных MoneyOrgTrack (лаб. работа №3)
-- Порядок создания: справочники -> основные таблицы -> таблица операций.

CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('income', 'expense'))
);

CREATE TABLE IF NOT EXISTS operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    operation_date TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_by INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users (user_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_operations_date ON operations (operation_date);
CREATE INDEX IF NOT EXISTS idx_operations_category ON operations (category_id);

-- Справочник ролей
INSERT OR IGNORE INTO roles (role_id, name) VALUES
    (1, 'admin'),
    (2, 'manager'),
    (3, 'employee');

-- Тестовые пользователи. Пароли: admin123 / manager123 / employee123.
-- Хеши получены PBKDF2-HMAC-SHA256 (120000 итераций, соли moneyorgtrack-*).
INSERT OR IGNORE INTO users (user_id, login, password_hash, full_name, role_id) VALUES
    (1, 'admin',
     'pbkdf2_sha256$120000$moneyorgtrack-admin$940b2f705f0a037c4f36cb1b64f8d1848e74f4a8670dafc8ed2f72a6130829f1',
     'Администратор системы', 1),
    (2, 'manager',
     'pbkdf2_sha256$120000$moneyorgtrack-manager$b6a285dd6b733ae5141ab3981df05e5ff179ec2a849bdf0c5713ef3fbb102c65',
     'Иван Петров', 2),
    (3, 'employee',
     'pbkdf2_sha256$120000$moneyorgtrack-employee$90f3b1104ac457d9d1daf045caa320970ecadabc15714f83122c043bd3524f5a',
     'Мария Смирнова', 3);

-- Пункты доходов и расходов
INSERT OR IGNORE INTO categories (category_id, name, kind) VALUES
    (1, 'Зарплата', 'income'),
    (2, 'Консультационные услуги', 'income'),
    (3, 'Аренда офиса', 'expense'),
    (4, 'Канцелярские товары', 'expense'),
    (5, 'Командировочные расходы', 'expense');

-- Тестовые операции за сентябрь и октябрь 2026 года
INSERT OR IGNORE INTO operations
    (operation_id, category_id, amount, operation_date, description, created_by)
VALUES
    (1, 1, 250000.00, '2026-09-05', 'Зарплата за сентябрь', 2),
    (2, 3, 45000.00, '2026-09-07', 'Аренда офиса, сентябрь', 2),
    (3, 4, 3200.00, '2026-09-15', 'Бумага и канцелярия', 2),
    (4, 2, 80000.00, '2026-09-20', 'Консультация клиента А', 2),
    (5, 1, 250000.00, '2026-10-05', 'Зарплата за октябрь', 2),
    (6, 2, 120000.00, '2026-10-11', 'Консультация клиента Б', 2),
    (7, 3, 45000.00, '2026-10-07', 'Аренда офиса, октябрь', 2),
    (8, 5, 18750.50, '2026-10-18', 'Командировка в Нижний Новгород', 2);
