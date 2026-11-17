"""Репозиторий пользователей."""

from __future__ import annotations

from ..database import get_connection
from ..models import User

_SELECT = """
    SELECT u.user_id, u.login, u.password_hash, u.full_name, u.role_id, r.name
    FROM users u
    JOIN roles r ON r.role_id = u.role_id
"""


def _map(row) -> User:
    return User(
        user_id=row["user_id"],
        login=row["login"],
        password_hash=row["password_hash"],
        full_name=row["full_name"],
        role_id=row["role_id"],
        role_name=row["name"],
    )


def create(login: str, password_hash: str, full_name: str, role_id: int) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO users (login, password_hash, full_name, role_id)
            VALUES (?, ?, ?, ?)
            """,
            (login, password_hash, full_name, role_id),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_by_id(user_id: int) -> User | None:
    connection = get_connection()
    try:
        row = connection.execute(_SELECT + " WHERE u.user_id = ?", (user_id,)).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_by_login(login: str) -> User | None:
    connection = get_connection()
    try:
        row = connection.execute(_SELECT + " WHERE u.login = ?", (login,)).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_all() -> list[User]:
    connection = get_connection()
    try:
        rows = connection.execute(_SELECT + " ORDER BY u.user_id").fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def delete(user_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()
