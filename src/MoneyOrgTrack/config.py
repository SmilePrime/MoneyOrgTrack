"""Конфигурация приложения MoneyOrgTrack."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "moneyorgtrack.db"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "out"


def get_db_path() -> Path:
    """Возвращает путь к файлу базы данных.

    Переменная окружения MONEYORGTRACK_DB позволяет использовать другую БД,
    в том числе временную в тестах.
    """
    value = os.environ.get("MONEYORGTRACK_DB")
    return Path(value) if value else DEFAULT_DB_PATH


def get_output_dir() -> Path:
    """Возвращает каталог для экспортных файлов лаб. работы №5."""
    value = os.environ.get("MONEYORGTRACK_OUT")
    return Path(value) if value else DEFAULT_OUTPUT_DIR
