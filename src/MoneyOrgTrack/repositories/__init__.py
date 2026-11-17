"""Репозитории — слой доступа к данным."""

from . import category_repository, operation_repository, role_repository, user_repository

__all__ = [
    "category_repository",
    "operation_repository",
    "role_repository",
    "user_repository",
]
