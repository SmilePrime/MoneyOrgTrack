"""Функции входа и регистрации для консольного интерфейса."""

from __future__ import annotations

from .services import AuthError, authenticate, register
from .services.auth_service import EMPLOYEE


def login():
    """Запрашивает логин и пароль, возвращает пользователя или None."""
    print("\n=== Авторизация ===")
    login_value = input("Логин: ").strip()
    password_value = input("Пароль: ").strip()

    user = authenticate(login_value, password_value)
    if user is None:
        print("\nНеверный логин или пароль")
        return None

    print(f"\nЗдравствуйте, {user.full_name}!")
    return user


def register_ui() -> None:
    """Регистрирует нового сотрудника через консоль."""
    print("\n=== Регистрация сотрудника ===")
    login_value = input("Логин: ").strip()
    password_value = input("Пароль: ").strip()
    full_name = input("ФИО: ").strip()

    try:
        register(login_value, password_value, full_name, EMPLOYEE)
        print("\nСотрудник зарегистрирован. Теперь выполните вход.")
    except AuthError as error:
        print(f"\nОшибка: {error}")
