"""Модель журнала операций (сущность OperationLog)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationLog:
    log_id: int
    user_id: int
    action: str
    details: str
    created_at: str
