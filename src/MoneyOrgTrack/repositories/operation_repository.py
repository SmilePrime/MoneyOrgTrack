"""Репозиторий FinancialItem — пунктов доходов и расходов."""

from __future__ import annotations

from ..database import get_connection, get_last_insert_id
from ..models import Operation

_SELECT = """
    SELECT i.itemID, i.userID, i.itemTypeID, i.name, i.amount,
           i.createdAt, i.updatedAt, t.name AS type_name, u.login
    FROM FinancialItem i
    JOIN ItemType t ON t.itemTypeID = i.itemTypeID
    JOIN "User" u ON u.userID = i.userID
"""


def _map(row) -> Operation:
    return Operation(
        operation_id=row["itemID"],
        user_id=row["userID"],
        item_type_id=row["itemTypeID"],
        name=row["name"],
        amount=row["amount"],
        created_at=row["createdAt"],
        updated_at=row["updatedAt"],
        category_name=row["type_name"],
        category_kind=row["type_name"],
        author_login=row["login"],
    )


def create(
    item_type_id: int,
    name: str,
    amount: float,
    created_at: str,
    user_id: int,
) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO FinancialItem
                (itemTypeID, name, amount, createdAt, updatedAt, userID)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_type_id, name, amount, created_at, created_at, user_id),
        )
        connection.commit()
        return get_last_insert_id(connection)
    finally:
        connection.close()


def get_by_id(operation_id: int) -> Operation | None:
    connection = get_connection()
    try:
        row = connection.execute(
            _SELECT + " WHERE i.itemID = ?", (operation_id,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_all(
    item_type_id: int | None = None,
    year: int | None = None,
    month: int | None = None,
) -> list[Operation]:
    conditions: list[str] = []
    parameters: list[object] = []
    if item_type_id is not None:
        conditions.append("i.itemTypeID = ?")
        parameters.append(item_type_id)
    if year is not None:
        conditions.append("substr(i.createdAt, 1, 4) = ?")
        parameters.append(f"{year:04d}")
    if month is not None:
        conditions.append("substr(i.createdAt, 6, 2) = ?")
        parameters.append(f"{month:02d}")

    sql = _SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY i.createdAt DESC, i.itemID DESC"

    connection = get_connection()
    try:
        rows = connection.execute(sql, parameters).fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def update(
    operation_id: int,
    item_type_id: int,
    name: str,
    amount: float,
    created_at: str,
) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            UPDATE FinancialItem
            SET itemTypeID = ?, name = ?, amount = ?, createdAt = ?,
                updatedAt = datetime('now')
            WHERE itemID = ?
            """,
            (item_type_id, name, amount, created_at, operation_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def update_amount(operation_id: int, amount: float) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            UPDATE FinancialItem
            SET amount = ?, updatedAt = datetime('now')
            WHERE itemID = ?
            """,
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
            "DELETE FROM FinancialItem WHERE itemID = ?", (operation_id,)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def get_totals(year: int, month: int) -> tuple[float, float]:
    """Возвращает пару (доходы, расходы) за месяц."""
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN t.name = 'income' THEN i.amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN t.name = 'expense' THEN i.amount ELSE 0 END), 0) AS expense
            FROM FinancialItem i
            JOIN ItemType t ON t.itemTypeID = i.itemTypeID
            WHERE substr(i.createdAt, 1, 4) = ?
              AND substr(i.createdAt, 6, 2) = ?
            """,
            (f"{year:04d}", f"{month:02d}"),
        ).fetchone()
        return float(row["income"]), float(row["expense"])
    finally:
        connection.close()
