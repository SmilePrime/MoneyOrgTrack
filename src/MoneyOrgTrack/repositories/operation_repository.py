"""Репозиторий финансовых операций (CRUD и агрегаты)."""

from __future__ import annotations

from ..database import get_connection
from ..models import Operation

_SELECT = """
    SELECT o.operation_id, o.category_id, o.amount, o.operation_date,
           o.description, o.created_by, c.name, c.kind, u.login
    FROM operations o
    JOIN categories c ON c.category_id = o.category_id
    JOIN users u ON u.user_id = o.created_by
"""


def _map(row) -> Operation:
    return Operation(
        operation_id=row["operation_id"],
        category_id=row["category_id"],
        amount=row["amount"],
        operation_date=row["operation_date"],
        description=row["description"],
        created_by=row["created_by"],
        category_name=row["name"],
        category_kind=row["kind"],
        author_login=row["login"],
    )


def create(
    category_id: int,
    amount: float,
    operation_date: str,
    description: str,
    created_by: int,
) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO operations
                (category_id, amount, operation_date, description, created_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (category_id, amount, operation_date, description, created_by),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_by_id(operation_id: int) -> Operation | None:
    connection = get_connection()
    try:
        row = connection.execute(
            _SELECT + " WHERE o.operation_id = ?", (operation_id,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_all(
    kind: str | None = None,
    year: int | None = None,
    month: int | None = None,
) -> list[Operation]:
    conditions: list[str] = []
    parameters: list[object] = []
    if kind:
        conditions.append("c.kind = ?")
        parameters.append(kind)
    if year is not None:
        conditions.append("substr(o.operation_date, 1, 4) = ?")
        parameters.append(f"{year:04d}")
    if month is not None:
        conditions.append("substr(o.operation_date, 6, 2) = ?")
        parameters.append(f"{month:02d}")

    sql = _SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY o.operation_date DESC, o.operation_id DESC"

    connection = get_connection()
    try:
        rows = connection.execute(sql, parameters).fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def update(
    operation_id: int,
    category_id: int,
    amount: float,
    operation_date: str,
    description: str,
) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            UPDATE operations
            SET category_id = ?, amount = ?, operation_date = ?, description = ?
            WHERE operation_id = ?
            """,
            (category_id, amount, operation_date, description, operation_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def update_amount(operation_id: int, amount: float) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE operations SET amount = ? WHERE operation_id = ?",
            (amount, operation_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete(operation_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM operations WHERE operation_id = ?", (operation_id,)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def get_totals(year: int, month: int) -> tuple[float, float]:
    """Возвращает пару (доходы, расходы) за указанный месяц."""
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN c.kind = 'income' THEN o.amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN c.kind = 'expense' THEN o.amount ELSE 0 END), 0) AS expense
            FROM operations o
            JOIN categories c ON c.category_id = o.category_id
            WHERE substr(o.operation_date, 1, 4) = ?
              AND substr(o.operation_date, 6, 2) = ?
            """,
            (f"{year:04d}", f"{month:02d}"),
        ).fetchone()
        return float(row["income"]), float(row["expense"])
    finally:
        connection.close()
