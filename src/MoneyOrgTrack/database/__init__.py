"""Слой работы с базой данных."""

from .database import get_connection, initialize_database

__all__ = ["get_connection", "initialize_database"]
