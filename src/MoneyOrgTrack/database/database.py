"""Подключение к SQLite и инициализация схемы базы данных."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_NAME = _PROJECT_ROOT / "data" / "moneyorgtrack.db"
_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Создаёт таблицы и начальные данные, если база ещё не создана."""
    if DB_NAME.exists():
        return

    DB_NAME.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection()
    try:
        connection.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()
    print("База данных создана.")
