"""Модель финансовой операции."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Operation:
    operation_id: int
    category_id: int
    amount: float
    operation_date: str
    description: str
    created_by: int
    # Вычисляемые поля, полученные JOIN-запросом (в БД не хранятся).
    category_name: str | None = None
    category_kind: str | None = None
    author_login: str | None = None

    @property
    def signed_amount(self) -> float:
        """Сумма со знаком: доход положительный, расход отрицательный."""
        if self.category_kind == "expense":
            return -self.amount
        return self.amount
