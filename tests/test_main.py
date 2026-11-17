"""Автоматические тесты MoneyOrgTrack (стандартный модуль unittest)."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.MoneyOrgTrack.database import get_connection, initialize_database, reset_database
from src.MoneyOrgTrack.repositories import (
    category_repository,
    monthly_report_repository,
    operation_log_repository,
    operation_repository,
    user_repository,
)
from src.MoneyOrgTrack.services import (
    AuthError,
    FinanceError,
    FinanceService,
    authenticate,
    export_data,
    hash_password,
    register,
    verify_password,
)


class MoneyOrgTrackTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.db_path = self.root / "test.db"
        self.old_db = os.environ.get("MONEYORGTRACK_DB")
        os.environ["MONEYORGTRACK_DB"] = str(self.db_path)
        reset_database()
        self.finance = FinanceService()

    def tearDown(self) -> None:
        if self.old_db is None:
            os.environ.pop("MONEYORGTRACK_DB", None)
        else:
            os.environ["MONEYORGTRACK_DB"] = self.old_db
        self.temporary.cleanup()

    def _user(self, login: str):
        user = user_repository.get_by_login(login)
        self.assertIsNotNone(user)
        return user

    def test_schema_matches_er_diagram_and_seed_data(self) -> None:
        connection = get_connection()
        try:
            counts = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in (
                    "Role",
                    "ItemType",
                    "User",
                    "FinancialItem",
                    "OperationLog",
                    "MonthlyReport",
                )
            }
        finally:
            connection.close()

        self.assertEqual(
            counts,
            {
                "Role": 3,
                "ItemType": 2,
                "User": 3,
                "FinancialItem": 8,
                "OperationLog": 3,
                "MonthlyReport": 2,
            },
        )
        self.assertEqual([item.name for item in category_repository.get_all()], ["income", "expense"])

    def test_password_hashing_and_authentication(self) -> None:
        encoded = hash_password("secret123", "fixed-salt")
        self.assertTrue(verify_password("secret123", encoded))
        self.assertFalse(verify_password("wrong", encoded))

        admin = self._user("admin")
        self.assertEqual(admin.role_name, "admin")
        self.assertEqual(admin.full_name, "Администратор системы")
        self.assertEqual(authenticate("admin", "admin123").user_id, admin.user_id)
        self.assertIsNone(authenticate("admin", "wrong-password"))
        self.assertIsNone(authenticate("missing", "admin123"))

    def test_register_user_and_duplicate_check(self) -> None:
        created = register("new_employee", "pass12345", "Новый Сотрудник")
        self.assertEqual(created.role_name, "employee")
        self.assertEqual(created.name, "Новый Сотрудник")

        with self.assertRaises(AuthError):
            register("new_employee", "pass12345", "Дубликат")
        with self.assertRaises(AuthError):
            register("another", "short", "Короткий пароль")
        with self.assertRaises(AuthError):
            register("another", "pass12345", "Неизвестная роль", "guest")

    def test_employee_cannot_change_data(self) -> None:
        employee = self._user("employee")
        with self.assertRaises(FinanceError):
            self.finance.add_category(employee, "income")
        with self.assertRaises(FinanceError):
            self.finance.add_operation(employee, 1, 1000, "2026-11-01")
        with self.assertRaises(FinanceError):
            self.finance.delete_operation(employee, 1)

    def test_item_type_crud(self) -> None:
        manager = self._user("manager")
        with self.assertRaises(FinanceError):
            self.finance.add_category(manager, "Дивиденды")  # только income/expense
        with self.assertRaises(FinanceError):
            self.finance.add_category(manager, "income")  # уже существует
        with self.assertRaises(FinanceError):
            self.finance.delete_category(manager, 1)  # есть FinancialItem

        item_type_id = category_repository.create("custom")
        self.assertEqual(category_repository.get_by_id(item_type_id).name, "custom")
        self.assertTrue(category_repository.update(item_type_id, "updated"))
        self.assertEqual(category_repository.get_by_id(item_type_id).name, "updated")
        self.assertTrue(category_repository.delete(item_type_id))
        self.assertIsNone(category_repository.get_by_id(item_type_id))

    def test_financial_item_crud_report_and_logs(self) -> None:
        manager = self._user("manager")

        report = self.finance.monthly_report(2026, 10, manager)
        self.assertEqual(report.income, 370000.0)
        self.assertEqual(report.expense, 63750.5)
        self.assertEqual(report.profit, 306249.5)
        # Повторный вызов обновляет существующую запись, а не создаёт новую.
        self.finance.monthly_report(2026, 10, manager)
        self.assertEqual(
            len(
                [
                    item
                    for item in monthly_report_repository.get_all()
                    if (item.year, item.month) == (2026, 10)
                    and item.user_id == manager.user_id
                ]
            ),
            1,
        )

        logs_before = len(operation_log_repository.get_all(limit=100))
        operation = self.finance.add_operation(
            manager, 1, 15000.5, "2026-11-03", "Тестовая консультация"
        )
        self.assertEqual(operation.name, "Тестовая консультация")
        self.assertEqual(operation.description, "Тестовая консультация")
        self.assertEqual(operation.operation_date, "2026-11-03")
        self.assertEqual(len(operation_log_repository.get_all(limit=100)), logs_before + 1)

        updated = self.finance.update_amount(manager, operation.operation_id, 16000)
        self.assertEqual(updated.amount, 16000)

        edited = self.finance.update_operation(
            manager, operation.operation_id, 2, 17000, "2026-11-04", "Изменённый пункт"
        )
        self.assertEqual(edited.category_kind, "expense")
        self.assertEqual(edited.name, "Изменённый пункт")

        november = self.finance.monthly_report(2026, 11, manager)
        self.assertEqual(november.expense, 17000)

        self.finance.delete_operation(manager, operation.operation_id)
        self.assertIsNone(operation_repository.get_by_id(operation.operation_id))

        with self.assertRaises(FinanceError):
            self.finance.add_operation(manager, 999, 100, "2026-11-05")
        with self.assertRaises(FinanceError):
            self.finance.add_operation(manager, 1, -100, "2026-11-05")
        with self.assertRaises(FinanceError):
            self.finance.add_operation(manager, 1, 100, "05.11.2026")
        with self.assertRaises(FinanceError):
            self.finance.monthly_report(2026, 13)

    def test_export_to_all_formats(self) -> None:
        output = self.root / "out"
        paths = export_data(output)
        self.assertEqual(set(paths), {"data.json", "data.csv", "data.xml", "data.yaml"})
        for path in paths.values():
            self.assertTrue(path.exists(), f"файл {path} не создан")

        records = json.loads(paths["data.json"].read_text(encoding="utf-8"))
        self.assertEqual(len(records), 8)
        self.assertEqual({record["kind"] for record in records}, {"income", "expense"})

        with paths["data.csv"].open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 8)
        self.assertIn("operation_id", rows[0])

        root = ET.parse(paths["data.xml"]).getroot()
        self.assertEqual(root.tag, "operations")
        self.assertEqual(len(root.findall("operation")), 8)

        yaml_text = paths["data.yaml"].read_text(encoding="utf-8")
        self.assertTrue(yaml_text.startswith("operations:\n  - operation_id:"))
        self.assertIn('category: "income"', yaml_text)

    def test_database_initialization_is_idempotent(self) -> None:
        initialize_database()
        initialize_database()
        self.assertEqual(len(operation_repository.get_all()), 8)


if __name__ == "__main__":
    unittest.main()
