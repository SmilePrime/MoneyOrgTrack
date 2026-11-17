-- Схема базы данных MoneyOrgTrack (лаб. работа №3)
-- Соответствует ER-диаграмме docs/diagram/er.png.
-- Порядок: справочники -> пользователи -> финансовые пункты -> журнал и отчёты.

CREATE TABLE IF NOT EXISTS Role (
    roleID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS ItemType (
    itemTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "User" (
    userID INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    passwordHash TEXT NOT NULL,
    roleID INTEGER NOT NULL,
    FOREIGN KEY (roleID) REFERENCES Role (roleID) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS FinancialItem (
    itemID INTEGER PRIMARY KEY AUTOINCREMENT,
    userID INTEGER NOT NULL,
    itemTypeID INTEGER NOT NULL,
    name TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    FOREIGN KEY (userID) REFERENCES "User" (userID) ON DELETE RESTRICT,
    FOREIGN KEY (itemTypeID) REFERENCES ItemType (itemTypeID) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS OperationLog (
    logID INTEGER PRIMARY KEY AUTOINCREMENT,
    userID INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    createdAt TEXT NOT NULL,
    FOREIGN KEY (userID) REFERENCES "User" (userID) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS MonthlyReport (
    reportID INTEGER PRIMARY KEY AUTOINCREMENT,
    userID INTEGER NOT NULL,
    month TEXT NOT NULL,
    incomeSum REAL NOT NULL DEFAULT 0,
    expenseSum REAL NOT NULL DEFAULT 0,
    profit REAL NOT NULL DEFAULT 0,
    createdAt TEXT NOT NULL,
    UNIQUE (userID, month),
    FOREIGN KEY (userID) REFERENCES "User" (userID) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_financial_item_date ON FinancialItem (createdAt);
CREATE INDEX IF NOT EXISTS idx_financial_item_type ON FinancialItem (itemTypeID);
CREATE INDEX IF NOT EXISTS idx_operation_log_user ON OperationLog (userID);

-- Справочник ролей
INSERT OR IGNORE INTO Role (roleID, name) VALUES
    (1, 'admin'),
    (2, 'manager'),
    (3, 'employee');

-- Типы пунктов финансового учёта
INSERT OR IGNORE INTO ItemType (itemTypeID, name) VALUES
    (1, 'income'),
    (2, 'expense');

-- Тестовые пользователи. Пароли: admin123 / manager123 / employee123.
-- Хеши получены PBKDF2-HMAC-SHA256 (120000 итераций, соли moneyorgtrack-*).
INSERT OR IGNORE INTO "User" (userID, name, login, passwordHash, roleID) VALUES
    (1, 'Администратор системы', 'admin',
     'pbkdf2_sha256$120000$moneyorgtrack-admin$940b2f705f0a037c4f36cb1b64f8d1848e74f4a8670dafc8ed2f72a6130829f1', 1),
    (2, 'Иван Петров', 'manager',
     'pbkdf2_sha256$120000$moneyorgtrack-manager$b6a285dd6b733ae5141ab3981df05e5ff179ec2a849bdf0c5713ef3fbb102c65', 2),
    (3, 'Мария Смирнова', 'employee',
     'pbkdf2_sha256$120000$moneyorgtrack-employee$90f3b1104ac457d9d1daf045caa320970ecadabc15714f83122c043bd3524f5a', 3);

-- Тестовые пункты доходов и расходов
INSERT OR IGNORE INTO FinancialItem
    (itemID, userID, itemTypeID, name, amount, createdAt, updatedAt)
VALUES
    (1, 2, 1, 'Зарплата за сентябрь', 250000.00, '2026-09-05 10:00:00', '2026-09-05 10:00:00'),
    (2, 2, 2, 'Аренда офиса, сентябрь', 45000.00, '2026-09-07 11:30:00', '2026-09-07 11:30:00'),
    (3, 2, 2, 'Бумага и канцелярия', 3200.00, '2026-09-15 09:15:00', '2026-09-15 09:15:00'),
    (4, 2, 1, 'Консультация клиента А', 80000.00, '2026-09-20 14:00:00', '2026-09-20 14:00:00'),
    (5, 2, 1, 'Зарплата за октябрь', 250000.00, '2026-10-05 10:00:00', '2026-10-05 10:00:00'),
    (6, 2, 1, 'Консультация клиента Б', 120000.00, '2026-10-11 15:20:00', '2026-10-11 15:20:00'),
    (7, 2, 2, 'Аренда офиса, октябрь', 45000.00, '2026-10-07 11:30:00', '2026-10-07 11:30:00'),
    (8, 2, 2, 'Командировка в Нижний Новгород', 18750.50, '2026-10-18 08:45:00', '2026-10-18 08:45:00');

-- Журнал действий
INSERT OR IGNORE INTO OperationLog (logID, userID, action, details, createdAt) VALUES
    (1, 2, 'CREATE', 'Создан пункт «Зарплата за октябрь»', '2026-10-05 10:00:00'),
    (2, 2, 'CREATE', 'Создан пункт «Консультация клиента Б»', '2026-10-11 15:20:00'),
    (3, 2, 'UPDATE', 'Изменён пункт #8', '2026-10-18 09:00:00');

-- Сохранённые месячные отчёты
INSERT OR IGNORE INTO MonthlyReport
    (reportID, userID, month, incomeSum, expenseSum, profit, createdAt)
VALUES
    (1, 1, '2026-09', 330000.00, 48200.00, 281800.00, '2026-10-01 00:00:00'),
    (2, 1, '2026-10', 370000.00, 63750.50, 306249.50, '2026-11-01 00:00:00');
