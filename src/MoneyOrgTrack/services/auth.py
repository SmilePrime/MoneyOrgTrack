"""Сервис аутентификации, регистрации и разграничения ролей."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from ..models import User
from ..repositories import role_repository, user_repository

ADMIN = "admin"
MANAGER = "manager"
EMPLOYEE = "employee"
ROLE_NAMES = (ADMIN, MANAGER, EMPLOYEE)

_ITERATIONS = 120_000
_ALGORITHM = "pbkdf2_sha256"


class AuthError(Exception):
    """Ошибка входа или регистрации пользователя."""


def hash_password(password: str, salt: str | None = None) -> str:
    """Возвращает строку вида algorithm$iterations$salt$hash."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    ).hex()
    return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    """Проверяет пароль против сохранённого хеша."""
    try:
        algorithm, iterations, salt, stored_hash = encoded.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return hmac.compare_digest(expected, stored_hash)
    except (ValueError, TypeError):
        return False


def authenticate(login: str, password: str) -> User | None:
    """Проверяет учётные данные и возвращает пользователя."""
    user = user_repository.get_by_login(login.strip())
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def register(
    login: str,
    password: str,
    full_name: str,
    role_name: str = EMPLOYEE,
) -> User:
    """Создаёт нового пользователя с указанной ролью."""
    login = login.strip()
    full_name = full_name.strip()
    role_name = role_name.strip().lower()

    if len(login) < 3:
        raise AuthError("Логин должен содержать минимум 3 символа")
    if len(password) < 6:
        raise AuthError("Пароль должен содержать минимум 6 символов")
    if not full_name:
        raise AuthError("ФИО не может быть пустым")
    if role_name not in ROLE_NAMES:
        raise AuthError("Недопустимая роль пользователя")
    if user_repository.get_by_login(login) is not None:
        raise AuthError("Пользователь с таким логином уже существует")

    role = role_repository.get_by_name(role_name)
    if role is None:
        raise AuthError("Роль не найдена в базе данных")

    user_repository.create(
        login=login,
        password_hash=hash_password(password),
        full_name=full_name,
        role_id=role.role_id,
    )
    created = user_repository.get_by_login(login)
    if created is None:  # защита от неожиданного состояния БД
        raise AuthError("Не удалось создать пользователя")
    return created
