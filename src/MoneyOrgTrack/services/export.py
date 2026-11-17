"""Экспорт данных в JSON, CSV, XML и YAML (лаб. работа №5)."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

from ..config import get_output_dir
from ..models import Operation
from ..repositories import operation_repository

EXPORT_FIELDS: tuple[str, ...] = (
    "operation_id",
    "category",
    "kind",
    "amount",
    "operation_date",
    "description",
    "author",
)


def _record_from_operation(operation: Operation) -> dict[str, Any]:
    """Преобразует модель в универсальную запись для всех форматов."""
    return {
        "operation_id": operation.operation_id,
        "category": operation.category_name or "",
        "kind": operation.category_kind or "",
        "amount": operation.amount,
        "operation_date": operation.operation_date,
        "description": operation.description,
        "author": operation.author_login or "",
    }


def build_records(operations: Iterable[Operation] | None = None) -> list[dict[str, Any]]:
    """Формирует список записей; при отсутствии аргумента читает все операции."""
    if operations is None:
        operations = operation_repository.get_all()
    return [_record_from_operation(operation) for operation in operations]


def _write_json(records: list[dict[str, Any]], path: Path) -> None:
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(EXPORT_FIELDS))
        writer.writeheader()
        writer.writerows(records)


def _write_xml(records: list[dict[str, Any]], path: Path) -> None:
    root = ET.Element("operations")
    for record in records:
        item = ET.SubElement(root, "operation")
        for field in EXPORT_FIELDS:
            element = ET.SubElement(item, field)
            element.text = str(record[field])
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # JSON-строка является корректной двойной кавычкой YAML.
    return json.dumps(str(value), ensure_ascii=False)


def _write_yaml(records: list[dict[str, Any]], path: Path) -> None:
    lines = ["operations:"]
    for record in records:
        lines.append(f"  - {EXPORT_FIELDS[0]}: {_yaml_scalar(record[EXPORT_FIELDS[0]])}")
        for field in EXPORT_FIELDS[1:]:
            lines.append(f"    {field}: {_yaml_scalar(record[field])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_data(output_dir: Path | str | None = None) -> dict[str, Path]:
    """Создаёт каталог out и четыре файла с текущими операциями."""
    directory = Path(output_dir) if output_dir is not None else get_output_dir()
    directory.mkdir(parents=True, exist_ok=True)

    records = build_records()
    writers = {
        "data.json": _write_json,
        "data.csv": _write_csv,
        "data.xml": _write_xml,
        "data.yaml": _write_yaml,
    }
    result: dict[str, Path] = {}
    for filename, writer in writers.items():
        path = directory / filename
        writer(records, path)
        result[filename] = path
    return result
