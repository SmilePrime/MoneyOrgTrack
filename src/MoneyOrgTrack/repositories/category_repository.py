"""Репозиторий справочника ItemType (тип дохода или расхода)."""

from __future__ import annotations

from ..database import get_connection
from ..models import ItemType


def _map(row) -> ItemType:
    return ItemType(item_type_id=row["itemTypeID"], name=row["name"])


def create(name: str, kind: str | None = None) -> int:
    """Создаёт тип. Параметр kind оставлен для совместимости со старым UI."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO ItemType (name) VALUES (?)", (name,)
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_by_id(item_type_id: int) -> ItemType | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT itemTypeID, name FROM ItemType WHERE itemTypeID = ?", (item_type_id,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_by_name(name: str) -> ItemType | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT itemTypeID, name FROM ItemType WHERE name = ?", (name,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_all(name: str | None = None) -> list[ItemType]:
    connection = get_connection()
    try:
        if name:
            rows = connection.execute(
                "SELECT itemTypeID, name FROM ItemType WHERE name = ? ORDER BY itemTypeID",
                (name,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT itemTypeID, name FROM ItemType ORDER BY itemTypeID"
            ).fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def update(item_type_id: int, name: str, kind: str | None = None) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE ItemType SET name = ? WHERE itemTypeID = ?", (name, item_type_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete(item_type_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM ItemType WHERE itemTypeID = ?", (item_type_id,)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()
