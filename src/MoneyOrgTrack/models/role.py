"""Модель роли пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    role_id: int
    name: str
