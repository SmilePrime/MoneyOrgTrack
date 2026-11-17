"""Модель пункта дохода или расхода."""

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
class Category:
    category_id: int
    name: str
    kind: str

    @property
    def kind_label(self) -> str:
        return KIND_LABELS.get(self.kind, self.kind)
