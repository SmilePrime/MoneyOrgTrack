"""Точка входа приложения MoneyOrgTrack."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from .ui import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="moneyorgtrack",
        description="Система контроля доходов и расходов организации",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    export_parser = subparsers.add_parser(
        "export", help="выгрузить операции в JSON, CSV, XML и YAML"
    )
    export_parser.add_argument(
        "--output", "-o", help="каталог для файлов (по умолчанию out/)"
    )
    return parser


def initialize_and_export(output: str | None) -> None:
    from .database import initialize_database
    from .services.export import export_data

    initialize_database()
    paths = export_data(output)
    print("Данные экспортированы:")
    for filename, path in paths.items():
        print(f"  {filename}: {path}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        initialize_and_export(args.output)
    else:
        run()


if __name__ == "__main__":
    main()
