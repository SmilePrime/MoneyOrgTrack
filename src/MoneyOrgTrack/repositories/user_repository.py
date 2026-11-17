"""Репозиторий пользователей (сущность User)."""

from __future__ import annotations

from ..database import get_connection, get_last_insert_id
from ..models import User

_SELECT = """
    SELECT u.userID, u.name, u.login, u.passwordHash, u.roleID, r.name AS role_name
    FROM "User" u
    JOIN Role r ON r.roleID = u.roleID
"""


def _map(row) -> User:
    return User(
        user_id=row["userID"],
        name=row["name"],
        login=row["login"],
        password_hash=row["passwordHash"],
        role_id=row["roleID"],
        role_name=row["role_name"],
    )


def create(login: str, password_hash: str, full_name: str, role_id: int) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO "User" (name, login, passwordHash, roleID)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, login, password_hash, role_id),
        )
        connection.commit()
        return get_last_insert_id(connection)
    finally:
        connection.close()


def get_by_id(user_id: int) -> User | None:
    connection = get_connection()
    try:
        row = connection.execute(_SELECT + " WHERE u.userID = ?", (user_id,)).fetchone()
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
        rows = connection.execute(_SELECT + " ORDER BY u.userID").fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def delete(user_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute('DELETE FROM "User" WHERE userID = ?', (user_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()
