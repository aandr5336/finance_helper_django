from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_positive_amount(value):
    """Сума має бути строго більшою за нуль."""
    if value is None:
        return
    if Decimal(value) <= 0:
        raise ValidationError('Сума має бути більшою за нуль.')
