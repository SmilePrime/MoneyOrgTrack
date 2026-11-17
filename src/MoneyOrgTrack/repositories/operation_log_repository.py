"""Репозиторий журнала действий (сущность OperationLog)."""

from __future__ import annotations

from ..database import get_connection, get_last_insert_id
from ..models import OperationLog


def _map(row) -> OperationLog:
    return OperationLog(
        log_id=row["logID"],
        user_id=row["userID"],
        action=row["action"],
        details=row["details"],
        created_at=row["createdAt"],
    )


def create(user_id: int, action: str, details: str) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO OperationLog (userID, action, details, createdAt)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (user_id, action, details),
        )
        connection.commit()
        return get_last_insert_id(connection)
    finally:
        connection.close()


def get_all(limit: int = 50) -> list[OperationLog]:
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT logID, userID, action, details, createdAt
            FROM OperationLog ORDER BY logID DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()
