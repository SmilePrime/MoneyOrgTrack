"""Репозиторий справочника ролей (сущность Role)."""

from __future__ import annotations

from ..database import get_connection
from ..models import Role


def _map(row) -> Role:
    return Role(role_id=row["roleID"], name=row["name"])


def get_all() -> list[Role]:
    connection = get_connection()
    try:
        rows = connection.execute("SELECT roleID, name FROM Role ORDER BY roleID").fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def get_by_id(role_id: int) -> Role | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT roleID, name FROM Role WHERE roleID = ?", (role_id,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_by_name(name: str) -> Role | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT roleID, name FROM Role WHERE name = ?", (name,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()
