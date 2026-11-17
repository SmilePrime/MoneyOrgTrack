"""Репозиторий пунктов доходов и расходов (CRUD)."""

from __future__ import annotations

from ..database import get_connection
from ..models import Category


def _map(row) -> Category:
    return Category(
        category_id=row["category_id"],
        name=row["name"],
        kind=row["kind"],
    )


def create(name: str, kind: str) -> int:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO categories (name, kind) VALUES (?, ?)", (name, kind)
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_by_id(category_id: int) -> Category | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT category_id, name, kind FROM categories WHERE category_id = ?",
            (category_id,),
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_by_name(name: str) -> Category | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT category_id, name, kind FROM categories WHERE name = ?", (name,)
        ).fetchone()
        return _map(row) if row else None
    finally:
        connection.close()


def get_all(kind: str | None = None) -> list[Category]:
    connection = get_connection()
    try:
        if kind:
            rows = connection.execute(
                """
                SELECT category_id, name, kind FROM categories
                WHERE kind = ? ORDER BY category_id
                """,
                (kind,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT category_id, name, kind FROM categories ORDER BY category_id"
            ).fetchall()
        return [_map(row) for row in rows]
    finally:
        connection.close()


def update(category_id: int, name: str, kind: str) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE categories SET name = ?, kind = ? WHERE category_id = ?",
            (name, kind, category_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete(category_id: int) -> bool:
    connection = get_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM categories WHERE category_id = ?", (category_id,)
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()
