"""Точка входа приложения MoneyOrgTrack."""

from __future__ import annotations

from .auth import login, register_ui
from .database import initialize_database
from .menu import editor_menu, viewer_menu
from .services.auth_service import ADMIN, EMPLOYEE, MANAGER


def main() -> None:
    initialize_database()

    while True:
        print("\n===== MoneyOrgTrack =====")
        print("1. Вход")
        print("2. Регистрация сотрудника")
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
        elif choice == "2":
            register_ui()
        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    main()
