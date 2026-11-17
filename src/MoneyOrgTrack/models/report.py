"""Модель MonthlyReport — сохранённый отчёт за месяц."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyReport:
    year: int
    month: int
    income: float
    expense: float
    # Поля заполняются при чтении сохранённого отчёта из таблицы MonthlyReport.
    report_id: int | None = None
    user_id: int | None = None
    created_at: str | None = None

    @property
    def profit(self) -> float:
        return round(self.income - self.expense, 2)
