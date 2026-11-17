"""Бизнес-логика учёта доходов и расходов."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from ..models import ItemType, MonthlyReport, Operation, User
from ..models.category import CATEGORY_KINDS
from ..repositories import (
    category_repository,
    monthly_report_repository,
    operation_log_repository,
    operation_repository,
)
from .auth import ADMIN, MANAGER

_EDIT_ROLES = {ADMIN, MANAGER}


class FinanceError(Exception):
    """Ошибка бизнес-логики финансового учёта."""


def _require_editor(user: User | None) -> None:
    if user is None or user.role_name not in _EDIT_ROLES:
        raise FinanceError("Изменять данные могут только руководитель и администратор")


def _validate_kind(kind: str) -> str:
    kind = kind.strip().lower()
    if kind not in CATEGORY_KINDS:
        raise FinanceError("Тип пункта должен быть income или expense")
    return kind


def _validate_date(value: str) -> str:
    value = value.strip().replace("T", " ")
    for pattern in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            datetime.strptime(value, pattern)
            if pattern == "%Y-%m-%d":
                return value + " 00:00:00"
            return value
        except ValueError:
            continue
    raise FinanceError("Дата должна быть в формате ГГГГ-ММ-ДД")


def _validate_amount(amount: float) -> float:
    amount = round(float(amount), 2)
    if amount <= 0:
        raise FinanceError("Сумма должна быть положительной")
    return amount


def _validate_period(year: int, month: int) -> tuple[int, int]:
    if not 1 <= month <= 12:
        raise FinanceError("Номер месяца должен быть от 1 до 12")
    if not 1900 <= year <= 9999:
        raise FinanceError("Некорректный год")
    return year, month


def _log(user: User, action: str, details: str) -> None:
    operation_log_repository.create(user.user_id, action, details)


class FinanceService:
    """Сервис, координирующий репозитории и проверяющий правила системы."""

    def list_categories(self, kind: str | None = None) -> list[ItemType]:
        if kind is not None:
            kind = _validate_kind(kind)
        return category_repository.get_all(kind)

    def add_category(self, user: User, name: str, kind: str | None = None) -> ItemType:
        _require_editor(user)
        type_name = _validate_kind(name or kind or "")
        if category_repository.get_by_name(type_name) is not None:
            raise FinanceError("Такой тип уже существует")
        item_type = category_repository.create(type_name)
        _log(user, "CREATE_ITEM_TYPE", f"Создан тип {type_name}")
        return item_type

    def update_category(
        self, user: User, category_id: int, name: str, kind: str | None = None
    ) -> ItemType:
        _require_editor(user)
        type_name = _validate_kind(name or kind or "")
        existing = category_repository.get_by_name(type_name)
        if existing is not None and existing.item_type_id != category_id:
            raise FinanceError("Такой тип уже существует")
        if not category_repository.update(category_id, type_name):
            raise FinanceError("Тип не найден")
        item_type = category_repository.get_by_id(category_id)
        if item_type is None:
            raise FinanceError("Тип не найден")
        _log(user, "UPDATE_ITEM_TYPE", f"Переименован тип #{category_id}")
        return item_type

    def delete_category(self, user: User, category_id: int) -> None:
        _require_editor(user)
        try:
            if not category_repository.delete(category_id):
                raise FinanceError("Тип не найден")
        except sqlite3.IntegrityError as error:
            raise FinanceError(
                "Нельзя удалить тип, по которому есть финансовые пункты"
            ) from error
        _log(user, "DELETE_ITEM_TYPE", f"Удалён тип #{category_id}")

    def list_operations(
        self,
        kind: str | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> list[Operation]:
        item_type_id = None
        if kind is not None:
            kind = _validate_kind(kind)
            item_type = category_repository.get_by_name(kind)
            if item_type is None:
                raise FinanceError("Тип не найден")
            item_type_id = item_type.item_type_id
        if year is not None or month is not None:
            _validate_period(year or 2000, month or 1)
        return operation_repository.get_all(item_type_id, year, month)

    def add_operation(
        self,
        user: User,
        category_id: int,
        amount: float,
        operation_date: str,
        description: str = "",
        created_by: int | None = None,
    ) -> Operation:
        _require_editor(user)
        if category_repository.get_by_id(category_id) is None:
            raise FinanceError("Тип пункта не найден")
        name = description.strip() or "Финансовый пункт"
        operation_id = operation_repository.create(
            item_type_id=category_id,
            name=name,
            amount=_validate_amount(amount),
            created_at=_validate_date(operation_date),
            user_id=created_by if created_by is not None else user.user_id,
        )
        _log(user, "CREATE_FINANCIAL_ITEM", f"Создан пункт #{operation_id}: {name}")
        operation = operation_repository.get_by_id(operation_id)
        if operation is None:
            raise FinanceError("Не удалось создать пункт")
        return operation

    def update_operation(
        self,
        user: User,
        operation_id: int,
        category_id: int,
        amount: float,
        operation_date: str,
        description: str,
    ) -> Operation:
        _require_editor(user)
        if category_repository.get_by_id(category_id) is None:
            raise FinanceError("Тип пункта не найден")
        if not operation_repository.update(
            operation_id,
            category_id,
            description.strip() or "Финансовый пункт",
            _validate_amount(amount),
            _validate_date(operation_date),
        ):
            raise FinanceError("Пункт не найден")
        _log(user, "UPDATE_FINANCIAL_ITEM", f"Изменён пункт #{operation_id}")
        operation = operation_repository.get_by_id(operation_id)
        if operation is None:
            raise FinanceError("Пункт не найден")
        return operation

    def update_amount(self, user: User, operation_id: int, amount: float) -> Operation:
        _require_editor(user)
        if not operation_repository.update_amount(operation_id, _validate_amount(amount)):
            raise FinanceError("Пункт не найден")
        _log(user, "UPDATE_AMOUNT", f"Изменена сумма пункта #{operation_id}")
        operation = operation_repository.get_by_id(operation_id)
        if operation is None:
            raise FinanceError("Пункт не найден")
        return operation

    def delete_operation(self, user: User, operation_id: int) -> None:
        _require_editor(user)
        if not operation_repository.delete(operation_id):
            raise FinanceError("Пункт не найден")
        _log(user, "DELETE_FINANCIAL_ITEM", f"Удалён пункт #{operation_id}")

    def monthly_report(
        self, year: int, month: int, user: User | None = None
    ) -> MonthlyReport:
        year, month = _validate_period(year, month)
        income, expense = operation_repository.get_totals(year, month)
        income = round(income, 2)
        expense = round(expense, 2)
        monthly_report_repository.save(
            user.user_id if user is not None else 1,
            f"{year:04d}-{month:02d}",
            income,
            expense,
        )
        return MonthlyReport(
            year=year,
            month=month,
            income=income,
            expense=expense,
        )

    def list_reports(self, user: User | None = None) -> list[MonthlyReport]:
        return monthly_report_repository.get_all(user.user_id if user else None)
