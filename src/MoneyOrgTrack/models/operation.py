"""Модель FinancialItem — пункт дохода или расхода."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Operation:
    """Запись таблицы FinancialItem.

    Названия полей датакласса приведены к терминам ER-диаграммы, а свойства
    ниже сохраняют совместимость с уже написанным кодом сервисов и UI.
    """

    operation_id: int
    user_id: int
    item_type_id: int
    name: str
    amount: float
    created_at: str
    updated_at: str
    # Вычисляемые поля из JOIN-запроса (в таблице FinancialItem не хранятся).
    category_name: str | None = None
    category_kind: str | None = None
    author_login: str | None = None

    @property
    def category_id(self) -> int:
        return self.item_type_id

    @property
    def created_by(self) -> int:
        return self.user_id

    @property
    def description(self) -> str:
        return self.name

    @property
    def operation_date(self) -> str:
        return self.created_at[:10]

    @property
    def signed_amount(self) -> float:
        if self.category_kind == "expense":
            return -self.amount
        return self.amount
