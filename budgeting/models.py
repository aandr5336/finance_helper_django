from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Category(models.Model):
    class CategoryType(models.TextChoices):
        EXPENSE = 'expense', 'Витрата'
        INCOME = 'income', 'Дохід'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # категорії належать користувачу — з ним і зникають
        related_name='categories',
        verbose_name='Власник',
    )
    name = models.CharField('Назва', max_length=100)
    icon = models.CharField('Іконка', max_length=50, default='tag')
    color = models.CharField('Колір', max_length=7, default='#6c757d')
    category_type = models.CharField(
        'Тип',
        max_length=10,
        choices=CategoryType.choices,
        default=CategoryType.EXPENSE,
    )
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name', 'category_type'],
                name='uniq_category_owner_name_type',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_category_type_display()})'

    def get_absolute_url(self):
        return reverse('budgeting:category_detail', kwargs={'pk': self.pk})


class Tag(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # теги особисті — cascade з власником
        related_name='tags',
        verbose_name='Власник',
    )
    name = models.CharField('Назва', max_length=50)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='uniq_tag_owner_name',
            ),
        ]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class TxType(models.TextChoices):
        EXPENSE = 'expense', 'Витрата'
        INCOME = 'income', 'Дохід'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # транзакції зникають разом із користувачем
        related_name='transactions',
        verbose_name='Власник',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # не можна видалити категорію з транзакціями
        related_name='transactions',
        verbose_name='Категорія',
    )
    amount = models.DecimalField('Сума', max_digits=12, decimal_places=2)
    tx_type = models.CharField('Тип', max_length=10, choices=TxType.choices)
    note = models.TextField('Примітка', blank=True)
    occurred_at = models.DateField('Дата операції')
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        related_name='transactions',
        blank=True,
        verbose_name='Теги',
    )

    class Meta:
        ordering = ['-occurred_at', '-id']
        verbose_name = 'Транзакція'
        verbose_name_plural = 'Транзакції'
        permissions = [
            ('can_view_all_transactions', 'Може переглядати всі транзакції'),
        ]

    def __str__(self):
        sign = '-' if self.tx_type == self.TxType.EXPENSE else '+'
        return f'{sign}{self.amount} · {self.category.name}'

    def get_absolute_url(self):
        return reverse('budgeting:transaction_detail', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({'amount': 'Сума має бути більшою за нуль.'})
        if self.category_id and self.tx_type and self.category.category_type != self.tx_type:
            raise ValidationError(
                {'category': 'Тип категорії має збігатися з типом транзакції.'}
            )


class Budget(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # бюджети особисті
        related_name='budgets',
        verbose_name='Власник',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,  # без категорії бюджет не має сенсу
        related_name='budgets',
        verbose_name='Категорія',
    )
    amount = models.DecimalField('Ліміт', max_digits=12, decimal_places=2)
    month = models.DateField('Місяць (перший день)')
    is_active = models.BooleanField('Активний', default=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['-month', 'category__name']
        verbose_name = 'Бюджет'
        verbose_name_plural = 'Бюджети'
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'category', 'month'],
                name='uniq_budget_owner_category_month',
            ),
        ]

    def __str__(self):
        return f'{self.category.name}: {self.amount} ({self.month:%Y-%m})'

    def get_absolute_url(self):
        return reverse('budgeting:budget_detail', kwargs={'pk': self.pk})

    @property
    def spent(self) -> Decimal:
        if hasattr(self, '_spent_cache'):
            return self._spent_cache
        total = (
            Transaction.objects.filter(
                owner=self.owner,
                category=self.category,
                tx_type=Transaction.TxType.EXPENSE,
                occurred_at__year=self.month.year,
                occurred_at__month=self.month.month,
            ).aggregate(s=models.Sum('amount'))['s']
            or Decimal('0')
        )
        return total

    @property
    def remaining(self) -> Decimal:
        return self.amount - self.spent

    @property
    def percent(self) -> float:
        if self.amount <= 0:
            return 0.0
        return float(min(self.spent / self.amount, Decimal('1')) * 100)

    @property
    def is_over(self) -> bool:
        return self.spent > self.amount


class SavingsGoal(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # цілі особисті
        related_name='savings_goals',
        verbose_name='Власник',
    )
    title = models.CharField('Назва', max_length=150)
    description = models.TextField('Опис', blank=True)
    target_amount = models.DecimalField('Цільова сума', max_digits=12, decimal_places=2)
    saved_amount = models.DecimalField(
        'Накопичено',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    deadline = models.DateField('Дедлайн', null=True, blank=True)
    is_done = models.BooleanField('Досягнуто', default=False)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['is_done', '-created_at']
        verbose_name = 'Фінансова ціль'
        verbose_name_plural = 'Фінансові цілі'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('budgeting:goal_detail', kwargs={'pk': self.pk})

    @property
    def percent(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        return float(min(self.saved_amount / self.target_amount, Decimal('1')) * 100)

    @property
    def remaining(self) -> Decimal:
        return max(self.target_amount - self.saved_amount, Decimal('0'))
