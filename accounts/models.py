from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Currency(models.TextChoices):
        UAH = 'UAH', 'Гривня (₴)'
        USD = 'USD', 'Долар США ($)'
        EUR = 'EUR', 'Євро (€)'
        GBP = 'GBP', 'Фунт стерлінгів (£)'
        PLN = 'PLN', 'Злотий (zł)'
        CHF = 'CHF', 'Швейцарський франк (Fr)'
        CZK = 'CZK', 'Чеська крона (Kč)'
        CAD = 'CAD', 'Канадський долар (C$)'
        CNY = 'CNY', 'Юань (¥)'
        JPY = 'JPY', 'Єна (¥)'
        TRY = 'TRY', 'Турецька ліра (₺)'
        AUD = 'AUD', 'Австралійський долар (A$)'
        RON = 'RON', 'Румунський лей (lei)'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # профіль існує лише разом із користувачем
        related_name='profile',
        verbose_name='Користувач',
    )
    preferred_currency = models.CharField(
        'Валюта відображення',
        max_length=3,
        choices=Currency.choices,
        default=Currency.UAH,
    )
    onboarding_dismissed = models.BooleanField(
        'Онбординг приховано',
        default=False,
    )
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'

    def __str__(self):
        return f'{self.user.username} · {self.preferred_currency}'
