"""Бизнес-логика учёта доходов и расходов."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from ..models import Category, MonthlyReport, Operation, User
from ..models.category import CATEGORY_KINDS
from ..repositories import category_repository, operation_repository
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
        raise FinanceError("Тип категории должен быть income или expense")
    return kind


def _validate_date(value: str) -> str:
    value = value.strip()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise FinanceError("Дата должна быть в формате ГГГГ-ММ-ДД") from error
    return value


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


class FinanceService:
    """Сервис, координирующий репозитории и проверяющий правила системы."""

    def list_categories(self, kind: str | None = None) -> list[Category]:
        if kind is not None:
            kind = _validate_kind(kind)
        return category_repository.get_all(kind)

    def add_category(self, user: User, name: str, kind: str) -> Category:
        _require_editor(user)
        name = name.strip()
        if not name:
            raise FinanceError("Название категории не может быть пустым")
        kind = _validate_kind(kind)
        if category_repository.get_by_name(name) is not None:
            raise FinanceError("Категория с таким названием уже существует")
        category_id = category_repository.create(name, kind)
        category = category_repository.get_by_id(category_id)
        if category is None:
            raise FinanceError("Не удалось создать категорию")
        return category

    def update_category(
        self, user: User, category_id: int, name: str, kind: str
    ) -> Category:
        _require_editor(user)
        name = name.strip()
        if not name:
            raise FinanceError("Название категории не может быть пустым")
        kind = _validate_kind(kind)
        existing = category_repository.get_by_name(name)
        if existing is not None and existing.category_id != category_id:
            raise FinanceError("Категория с таким названием уже существует")
        if not category_repository.update(category_id, name, kind):
            raise FinanceError("Категория не найдена")
        category = category_repository.get_by_id(category_id)
        if category is None:
            raise FinanceError("Категория не найдена")
        return category

    def delete_category(self, user: User, category_id: int) -> None:
        _require_editor(user)
        try:
            if not category_repository.delete(category_id):
                raise FinanceError("Категория не найдена")
        except sqlite3.IntegrityError as error:
            raise FinanceError(
                "Нельзя удалить категорию, по которой есть операции"
            ) from error

    def list_operations(
        self,
        kind: str | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> list[Operation]:
        if kind is not None:
            kind = _validate_kind(kind)
        if year is not None or month is not None:
            _validate_period(year or 2000, month or 1)
        return operation_repository.get_all(kind, year, month)

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
        category = category_repository.get_by_id(category_id)
        if category is None:
            raise FinanceError("Категория не найдена")
        operation_id = operation_repository.create(
            category_id=category_id,
            amount=_validate_amount(amount),
            operation_date=_validate_date(operation_date),
            description=description.strip(),
            created_by=created_by if created_by is not None else user.user_id,
        )
        operation = operation_repository.get_by_id(operation_id)
        if operation is None:
            raise FinanceError("Не удалось создать операцию")
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
            raise FinanceError("Категория не найдена")
        if not operation_repository.update(
            operation_id,
            category_id,
            _validate_amount(amount),
            _validate_date(operation_date),
            description.strip(),
        ):
            raise FinanceError("Операция не найдена")
        operation = operation_repository.get_by_id(operation_id)
        if operation is None:
            raise FinanceError("Операция не найдена")
        return operation

    def update_amount(self, user: User, operation_id: int, amount: float) -> Operation:
        _require_editor(user)
        if not operation_repository.update_amount(operation_id, _validate_amount(amount)):
            raise FinanceError("Операция не найдена")
        operation = operation_repository.get_by_id(operation_id)
        if operation is None:
            raise FinanceError("Операция не найдена")
        return operation

    def delete_operation(self, user: User, operation_id: int) -> None:
        _require_editor(user)
        if not operation_repository.delete(operation_id):
            raise FinanceError("Операция не найдена")

    def monthly_report(self, year: int, month: int) -> MonthlyReport:
        year, month = _validate_period(year, month)
        income, expense = operation_repository.get_totals(year, month)
        return MonthlyReport(
            year=year,
            month=month,
            income=round(income, 2),
            expense=round(expense, 2),
        )
