"""Функция входа для консольного интерфейса."""

from __future__ import annotations

from .services import authenticate


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