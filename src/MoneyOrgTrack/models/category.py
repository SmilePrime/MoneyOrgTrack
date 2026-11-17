"""Модель справочника ItemType (тип пункта дохода/расхода)."""

from __future__ import annotations

from dataclasses import dataclass

KIND_INCOME = "income"
KIND_EXPENSE = "expense"
CATEGORY_KINDS = (KIND_INCOME, KIND_EXPENSE)

KIND_LABELS = {
    KIND_INCOME: "доход",
    KIND_EXPENSE: "расход",
}


@dataclass
class ItemType:
    item_type_id: int
    name: str

    # Свойства-алиасы сохраняют совместимость с кодом, который называл
    # этот справочник "категориями".
    @property
    def category_id(self) -> int:
        return self.item_type_id

    @property
    def kind(self) -> str:
        return self.name

    @property
    def kind_label(self) -> str:
        return KIND_LABELS.get(self.name, self.name)


Category = ItemType
