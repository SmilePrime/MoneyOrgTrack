"""Модель отчёта за месяц."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyReport:
    year: int
    month: int
    income: float
    expense: float

    @property
    def profit(self) -> float:
        return round(self.income - self.expense, 2)
