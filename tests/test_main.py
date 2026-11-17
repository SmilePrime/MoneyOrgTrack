"""Автоматические тесты MoneyOrgTrack (стандартный модуль unittest)."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.MoneyOrgTrack.database import get_connection, reset_database
from src.MoneyOrgTrack.repositories import category_repository, operation_repository, user_repository
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

    def test_schema_and_seed_data(self) -> None:
        connection = get_connection()
        try:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("roles", "users", "categories", "operations")
            }
        finally:
            connection.close()

        self.assertEqual(counts, {"roles": 3, "users": 3, "categories": 5, "operations": 8})
        self.assertEqual(len(category_repository.get_all("income")), 2)
        self.assertEqual(len(category_repository.get_all("expense")), 3)

    def test_password_hashing_and_authentication(self) -> None:
        encoded = hash_password("secret123", "fixed-salt")
        self.assertTrue(verify_password("secret123", encoded))
        self.assertFalse(verify_password("wrong", encoded))

        admin = self._user("admin")
        self.assertEqual(admin.role_name, "admin")
        self.assertEqual(authenticate("admin", "admin123").user_id, admin.user_id)
        self.assertIsNone(authenticate("admin", "wrong-password"))
        self.assertIsNone(authenticate("missing", "admin123"))

    def test_register_user_and_duplicate_check(self) -> None:
        created = register("new_employee", "pass12345", "Новый Сотрудник")
        self.assertEqual(created.role_name, "employee")
        self.assertEqual(created.full_name, "Новый Сотрудник")

        with self.assertRaises(AuthError):
            register("new_employee", "pass12345", "Дубликат")
        with self.assertRaises(AuthError):
            register("another", "short", "Короткий пароль")
        with self.assertRaises(AuthError):
            register("another", "pass12345", "Неизвестная роль", "guest")

    def test_employee_cannot_change_data(self) -> None:
        employee = self._user("employee")
        with self.assertRaises(FinanceError):
            self.finance.add_category(employee, "Новая категория", "income")
        with self.assertRaises(FinanceError):
            self.finance.add_operation(employee, 1, 1000, "2026-11-01")
        with self.assertRaises(FinanceError):
            self.finance.delete_operation(employee, 1)

    def test_category_crud(self) -> None:
        manager = self._user("manager")
        category = self.finance.add_category(manager, "Дивиденды", "income")
        self.assertEqual(category.kind, "income")

        updated = self.finance.update_category(manager, category.category_id, "Дивиденды", "expense")
        self.assertEqual(updated.kind, "expense")

        with self.assertRaises(FinanceError):
            self.finance.delete_category(manager, 1)  # есть связанные операции

        self.finance.delete_category(manager, category.category_id)
        self.assertIsNone(category_repository.get_by_id(category.category_id))

    def test_operation_crud_and_monthly_report(self) -> None:
        manager = self._user("manager")

        report = self.finance.monthly_report(2026, 10)
        self.assertEqual(report.income, 370000.0)
        self.assertEqual(report.expense, 63750.5)
        self.assertEqual(report.profit, 306249.5)

        operation = self.finance.add_operation(
            manager, 2, 15000.5, "2026-11-03", "Тестовая консультация"
        )
        self.assertEqual(operation.category_name, "Консультационные услуги")

        updated = self.finance.update_amount(manager, operation.operation_id, 16000)
        self.assertEqual(updated.amount, 16000)

        edited = self.finance.update_operation(
            manager, operation.operation_id, 4, 17000, "2026-11-04", "Изменённая операция"
        )
        self.assertEqual(edited.category_kind, "expense")
        self.assertEqual(edited.description, "Изменённая операция")

        november = self.finance.monthly_report(2026, 11)
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
        self.assertIn('category: "Зарплата"', yaml_text)

    def test_database_initialization_is_idempotent(self) -> None:
        from src.MoneyOrgTrack.database import initialize_database

        initialize_database()
        initialize_database()
        self.assertEqual(len(operation_repository.get_all()), 8)


if __name__ == "__main__":
    unittest.main()
