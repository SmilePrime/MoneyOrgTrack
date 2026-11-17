"""Репозиторий сохранённых месячных отчётов (сущность MonthlyReport)."""

from __future__ import annotations

from ..database import get_connection
from ..models import MonthlyReport


def _map(row) -> MonthlyReport:
    return MonthlyReport(
        year=int(row["month"][:4]),
        month=int(row["month"][5:7]),
        income=row["incomeSum"],
        expense=row["expenseSum"],
        report_id=row["reportID"],
        user_id=row["userID"],
        created_at=row["createdAt"],
    )


def save(user_id: int, month: str, income: float, expense: float) -> None:
    """Сохраняет (обновляет) отчёт за месяц для пользователя."""
    profit = round(income - expense, 2)
    connection = get_connection()
    try:
        connection.execute(
            "DELETE FROM MonthlyReport WHERE userID = ? AND month = ?",
            (user_id, month),
        )
        connection.execute(
            """
            INSERT INTO MonthlyReport
                (userID, month, incomeSum, expenseSum, profit, createdAt)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (user_id, month, income, expense, profit),
        )
        connection.commit()
    finally:
        connection.close()


def get_all(user_id: int | None = None) -> list[MonthlyReport]:
    connection = get_connection()
    try:
        if user_id is None:
            rows = connection.execute(
                """
                SELECT reportID, userID, month, incomeSum, expenseSum, createdAt
                FROM MonthlyReport ORDER BY month DESC, reportID DESC
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT reportID, userID, month, incomeSum, expenseSum, createdAt
                FROM MonthlyReport WHERE userID = ? ORDER BY month DESC, reportID DESC
                """,
                (user_id,),
            ).fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()
