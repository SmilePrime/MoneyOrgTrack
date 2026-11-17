"""Консольный пользовательский интерфейс MoneyOrgTrack."""

from __future__ import annotations

from ..database import initialize_database
from ..models import Category, Operation, User
from ..repositories import user_repository
from ..services import (
    AuthError,
    FinanceError,
    FinanceService,
    authenticate,
    export_data,
    register,
)
from ..services.auth import ADMIN, EMPLOYEE, MANAGER, ROLE_NAMES

finance = FinanceService()

_KIND_LABELS = {"income": "доход", "expense": "расход"}


def _prompt(message: str) -> str:
    return input(message).strip()


def _read_int(message: str) -> int | None:
    value = _prompt(message)
    try:
        return int(value)
    except ValueError:
        print("Ошибка: введите целое число")
        return None


def _read_float(message: str) -> float | None:
    value = _prompt(message).replace(",", ".")
    try:
        return float(value)
    except ValueError:
        print("Ошибка: введите число")
        return None


def _print_operations(operations: list[Operation]) -> None:
    if not operations:
        print("Операции не найдены.")
        return
    print(f"\n{'ID':>4}  {'Дата':<12} {'Тип':<8} {'Сумма':>12}  Категория / описание")
    print("-" * 72)
    for operation in operations:
        kind = _KIND_LABELS.get(operation.category_kind or "", operation.category_kind or "")
        sign = "+" if operation.category_kind == "income" else "-"
        print(
            f"{operation.operation_id:>4}  {operation.operation_date:<12} "
            f"{kind:<8} {sign}{operation.amount:>11.2f}  "
            f"{operation.category_name} / {operation.description}"
        )


def _print_categories(categories: list[Category]) -> None:
    if not categories:
        print("Категории не найдены.")
        return
    print(f"\n{'ID':>4}  {'Тип':<8} Название")
    print("-" * 40)
    for category in categories:
        print(
            f"{category.category_id:>4}  "
            f"{_KIND_LABELS.get(category.kind, category.kind):<8} {category.name}"
        )


def _choose_category(kind: str | None = None) -> int | None:
    categories = finance.list_categories(kind)
    _print_categories(categories)
    if not categories:
        return None
    category_id = _read_int("ID категории: ")
    if category_id is None:
        return None
    if not any(item.category_id == category_id for item in categories):
        print("Категория с таким ID не найдена")
        return None
    return category_id


def _categories_menu(user: User) -> None:
    while True:
        print("\n===== Типы доходов и расходов (ItemType) =====")
        print("1. Показать все")
        print("2. Показать доходы")
        print("3. Показать расходы")
        print("4. Добавить")
        print("5. Переименовать")
        print("6. Удалить")
        print("0. Назад")
        choice = _prompt("Выберите действие: ")

        try:
            if choice == "1":
                _print_categories(finance.list_categories())
            elif choice == "2":
                _print_categories(finance.list_categories("income"))
            elif choice == "3":
                _print_categories(finance.list_categories("expense"))
            elif choice == "4":
                kind = _prompt("Тип (income/expense): ")
                item_type = finance.add_category(user, kind)
                print(f"Тип #{item_type.category_id} добавлен")
            elif choice == "5":
                category_id = _read_int("ID типа: ")
                if category_id is not None:
                    name = _prompt("Новое название (income/expense): ")
                    finance.update_category(user, category_id, name)
                    print("Тип обновлён")
            elif choice == "6":
                category_id = _read_int("ID типа: ")
                if category_id is not None:
                    finance.delete_category(user, category_id)
                    print("Тип удалён")
            elif choice == "0":
                return
            else:
                print("Неизвестный пункт меню")
        except FinanceError as error:
            print(f"Ошибка: {error}")


def _operations_menu(user: User) -> None:
    while True:
        print("\n===== Операции =====")
        print("1. Показать все")
        print("2. Показать доходы")
        print("3. Показать расходы")
        print("4. Добавить")
        print("5. Изменить сумму")
        print("6. Изменить операцию")
        print("7. Удалить")
        print("0. Назад")
        choice = _prompt("Выберите действие: ")

        try:
            if choice in {"1", "2", "3"}:
                kind = {"1": None, "2": "income", "3": "expense"}[choice]
                _print_operations(finance.list_operations(kind))
            elif choice == "4":
                category_id = _choose_category()
                if category_id is not None:
                    amount = _read_float("Сумма: ")
                    operation_date = _prompt("Дата (ГГГГ-ММ-ДД): ")
                    description = _prompt("Описание: ")
                    if amount is not None:
                        operation = finance.add_operation(
                            user, category_id, amount, operation_date, description
                        )
                        print(f"Операция #{operation.operation_id} добавлена")
            elif choice == "5":
                operation_id = _read_int("ID операции: ")
                amount = _read_float("Новая сумма: ")
                if operation_id is not None and amount is not None:
                    finance.update_amount(user, operation_id, amount)
                    print("Сумма обновлена")
            elif choice == "6":
                operation_id = _read_int("ID операции: ")
                if operation_id is not None:
                    current = next(
                        (
                            item
                            for item in finance.list_operations()
                            if item.operation_id == operation_id
                        ),
                        None,
                    )
                    if current is None:
                        print("Операция не найдена")
                        continue
                    category_id = _choose_category()
                    amount = _read_float(f"Сумма [{current.amount}]: ")
                    operation_date = _prompt(f"Дата [{current.operation_date}]: ")
                    description = _prompt(f"Описание [{current.description}]: ")
                    if category_id is not None and amount is not None:
                        finance.update_operation(
                            user,
                            operation_id,
                            category_id,
                            amount,
                            operation_date or current.operation_date,
                            description or current.description,
                        )
                        print("Операция обновлена")
            elif choice == "7":
                operation_id = _read_int("ID операции: ")
                if operation_id is not None:
                    finance.delete_operation(user, operation_id)
                    print("Операция удалена")
            elif choice == "0":
                return
            else:
                print("Неизвестный пункт меню")
        except FinanceError as error:
            print(f"Ошибка: {error}")


def _report(user: User) -> None:
    year = _read_int("Год: ")
    month = _read_int("Месяц: ")
    if year is None or month is None:
        return
    try:
        report = finance.monthly_report(year, month, user)
    except FinanceError as error:
        print(f"Ошибка: {error}")
        return
    print(f"\nОтчёт за {report.month:02d}.{report.year}")
    print(f"  Доходы:  {report.income:>12.2f}")
    print(f"  Расходы: {report.expense:>12.2f}")
    print(f"  Прибыль: {report.profit:>12.2f}")


def _do_export() -> None:
    try:
        paths = export_data()
    except OSError as error:
        print(f"Ошибка экспорта: {error}")
        return
    print("Данные экспортированы:")
    for filename, path in paths.items():
        print(f"  {filename}: {path}")


def _users_menu() -> None:
    while True:
        print("\n===== Пользователи =====")
        print("1. Список")
        print("2. Добавить")
        print("3. Удалить")
        print("0. Назад")
        choice = _prompt("Выберите действие: ")

        try:
            if choice == "1":
                users = user_repository.get_all()
                print(f"\n{'ID':>4}  {'Логин':<15} {'Роль':<10} ФИО")
                print("-" * 55)
                for user in users:
                    print(
                        f"{user.user_id:>4}  {user.login:<15} "
                        f"{user.role_name:<10} {user.full_name}"
                    )
            elif choice == "2":
                login = _prompt("Логин: ")
                password = _prompt("Пароль: ")
                full_name = _prompt("ФИО: ")
                print("Роли: " + ", ".join(ROLE_NAMES))
                role_name = _prompt("Роль: ")
                created = register(login, password, full_name, role_name)
                print(f"Пользователь #{created.user_id} создан")
            elif choice == "3":
                user_id = _read_int("ID пользователя: ")
                if user_id is not None:
                    if user_id == 1:
                        print("Нельзя удалить встроенного администратора")
                    elif user_repository.delete(user_id):
                        print("Пользователь удалён")
                    else:
                        print("Пользователь не найден")
            elif choice == "0":
                return
            else:
                print("Неизвестный пункт меню")
        except AuthError as error:
            print(f"Ошибка: {error}")


def _view_menu(user: User) -> None:
    while True:
        print(f"\n===== Просмотр ({user.role_name}) =====")
        print("1. Список доходов и расходов")
        print("2. Отчёт за месяц")
        print("3. Экспорт данных")
        print("0. Выйти")
        choice = _prompt("Выберите действие: ")
        if choice == "1":
            _print_operations(finance.list_operations())
        elif choice == "2":
            _report(user)
        elif choice == "3":
            _do_export()
        elif choice == "0":
            return
        else:
            print("Неизвестный пункт меню")


def _editor_menu(user: User) -> None:
    while True:
        print(f"\n===== Главное меню ({user.role_name}: {user.full_name}) =====")
        print("1. Типы доходов и расходов")
        print("2. Пункты доходов и расходов")
        print("3. Отчёт за месяц")
        print("4. Экспорт данных")
        if user.role_name == ADMIN:
            print("5. Пользователи")
        print("0. Выйти")
        choice = _prompt("Выберите действие: ")

        if choice == "1":
            _categories_menu(user)
        elif choice == "2":
            _operations_menu(user)
        elif choice == "3":
            _report(user)
        elif choice == "4":
            _do_export()
        elif choice == "5" and user.role_name == ADMIN:
            _users_menu()
        elif choice == "0":
            return
        else:
            print("Неизвестный пункт меню")


def login_menu() -> None:
    """Авторизация и регистрация сотрудника."""
    while True:
        print("\n===== MoneyOrgTrack =====")
        print("1. Вход в систему")
        print("2. Регистрация сотрудника")
        print("0. Выход")
        choice = _prompt("Выберите действие: ")

        if choice == "1":
            login = _prompt("Логин: ")
            password = _prompt("Пароль: ")
            user = authenticate(login, password)
            if user is None:
                print("Неверный логин или пароль")
                continue
            print(f"Здравствуйте, {user.full_name}!")
            if user.role_name == EMPLOYEE:
                _view_menu(user)
            elif user.role_name in {ADMIN, MANAGER}:
                _editor_menu(user)
            else:
                print("У пользователя не назначена роль")
        elif choice == "2":
            try:
                login = _prompt("Логин: ")
                password = _prompt("Пароль: ")
                full_name = _prompt("ФИО: ")
                register(login, password, full_name, EMPLOYEE)
                print("Сотрудник зарегистрирован. Теперь выполните вход.")
            except AuthError as error:
                print(f"Ошибка: {error}")
        elif choice == "0":
            return
        else:
            print("Неизвестный пункт меню")


def run() -> None:
    """Запуск интерактивного приложения."""
    initialize_database()
    login_menu()


def run_export() -> None:
    """Экспорт данных без интерактивного меню."""
    initialize_database()
    _do_export()
