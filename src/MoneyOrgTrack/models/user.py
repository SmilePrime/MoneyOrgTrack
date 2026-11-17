"""Модель пользователя системы (сущность User по ER-диаграмме)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    name: str
    login: str
    password_hash: str
    role_id: int
    role_name: str | None = None

    @property
    def full_name(self) -> str:
        """Алиас для совместимости с пользовательским интерфейсом."""
        return self.name
