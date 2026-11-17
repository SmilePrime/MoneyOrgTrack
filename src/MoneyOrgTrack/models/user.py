"""Модель пользователя системы."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    login: str
    password_hash: str
    full_name: str
    role_id: int
    role_name: str | None = None
