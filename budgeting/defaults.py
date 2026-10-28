"""Стартові дані для нового користувача (категорії тощо)."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser

from .models import Category

DEFAULT_CATEGORIES: list[tuple[str, str, str, str]] = [
    ('Їжа', 'restaurant', '#FF9800', Category.CategoryType.EXPENSE),
    ('Транспорт', 'bus', '#2196F3', Category.CategoryType.EXPENSE),
    ('Житло', 'home', '#FFC107', Category.CategoryType.EXPENSE),
    ('Розваги', 'movie', '#9C27B0', Category.CategoryType.EXPENSE),
    ('Зарплата', 'payments', '#4CAF50', Category.CategoryType.INCOME),
    ('Фріланс', 'work', '#009688', Category.CategoryType.INCOME),
]


def ensure_default_categories(user: AbstractBaseUser) -> int:
    """Створює базові категорії, якщо в користувача ще немає жодної активної.

    Повертає кількість створених записів.
    """
    if Category.objects.filter(owner=user, is_active=True).exists():
        return 0

    created = 0
    for name, icon, color, ctype in DEFAULT_CATEGORIES:
        _, was_created = Category.objects.get_or_create(
            owner=user,
            name=name,
            category_type=ctype,
            defaults={
                'icon': icon,
                'color': color,
                'is_active': True,
            },
        )
        if was_created:
            created += 1
    return created
