"""Подключение к SQLite и инициализация схемы базы данных."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import get_db_path

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Открывает соединение с базой данных SQLite."""
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _execute_script(script: str, db_path: Path | str | None = None) -> None:
    connection = get_connection(db_path)
    try:
        connection.executescript(script)
        connection.commit()
    finally:
        connection.close()


def initialize_database(db_path: Path | str | None = None) -> None:
    """Создаёт таблицы и начальные данные, если их ещё нет.

    Функция безопасна для повторного вызова: существующие записи не удаляются.
    """
    _execute_script(_SCHEMA_PATH.read_text(encoding="utf-8"), db_path)


def reset_database(db_path: Path | str | None = None) -> None:
    """Удаляет все таблицы и создаёт базу заново (для разработки и тестов)."""
    drop_script = """
    DROP TABLE IF EXISTS MonthlyReport;
    DROP TABLE IF EXISTS OperationLog;
    DROP TABLE IF EXISTS FinancialItem;
    DROP TABLE IF EXISTS "User";
    DROP TABLE IF EXISTS ItemType;
    DROP TABLE IF EXISTS Role;
    """
    _execute_script(drop_script, db_path)
    initialize_database(db_path)
