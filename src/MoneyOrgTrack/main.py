"""Точка входа приложения MoneyOrgTrack."""

from __future__ import annotations

import sys
from pathlib import Path

# Позволяет запускать файл напрямую из IDE без ошибки relative import.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "src.MoneyOrgTrack"

from .auth import login
from .database import initialize_database
from .menu import editor_menu, viewer_menu
from .services.auth_service import ADMIN, EMPLOYEE, MANAGER


def main() -> None:
    initialize_database()

    while True:
        print("\n===== MoneyOrgTrack =====")
        print("1. Вход")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            user = login()
            if user is None:
                continue
            if user.role_name in {ADMIN, MANAGER}:
                editor_menu(user)
            elif user.role_name == EMPLOYEE:
                viewer_menu(user)
            else:
                print("У пользователя не назначена роль")
        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    main()