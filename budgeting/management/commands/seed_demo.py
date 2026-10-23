from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

from budgeting.models import Budget, Category, SavingsGoal, Tag, Transaction


class Command(BaseCommand):
    help = 'Створює демо-користувачів, категорії, транзакції, бюджети та цілі'

    @transaction.atomic
    def handle(self, *args, **options):
        users_group, _ = Group.objects.get_or_create(name='users')
        analysts, _ = Group.objects.get_or_create(name='analysts')
        perm = Permission.objects.filter(codename='can_view_all_transactions').first()
        if perm:
            analysts.permissions.add(perm)

        demo, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@budgetflow.local'},
        )
        if created:
            demo.set_password('demo12345')
            demo.save()
        demo.groups.add(users_group)

        analyst, created = User.objects.get_or_create(
            username='analyst',
            defaults={'email': 'analyst@budgetflow.local', 'is_staff': True},
        )
        if created:
            analyst.set_password('analyst12345')
            analyst.save()
        analyst.groups.add(users_group, analysts)

        if Transaction.objects.filter(owner=demo).exists():
            self.stdout.write(self.style.WARNING('Демо-дані вже є — пропуск наповнення.'))
            return

        cats_data = [
            ('Їжа', 'restaurant', '#FF9800', 'expense'),
            ('Транспорт', 'bus', '#2196F3', 'expense'),
            ('Житло', 'home', '#FFC107', 'expense'),
            ('Розваги', 'movie', '#9C27B0', 'expense'),
            ('Зарплата', 'payments', '#4CAF50', 'income'),
            ('Фріланс', 'work', '#009688', 'income'),
        ]
        cats = {}
        for name, icon, color, ctype in cats_data:
            cats[name] = Category.objects.create(
                owner=demo, name=name, icon=icon, color=color, category_type=ctype,
            )

        tags = [
            Tag.objects.create(owner=demo, name='необхідне'),
            Tag.objects.create(owner=demo, name='імпульс'),
            Tag.objects.create(owner=demo, name='робота'),
        ]

        today = date.today()
        month_start = today.replace(day=1)
        samples = [
            ('Зарплата', 'income', Decimal('28000'), 'Основна зарплата', 2),
            ('Фріланс', 'income', Decimal('4500'), 'Проєкт A', 5),
            ('Їжа', 'expense', Decimal('850'), 'Продукти', 3),
            ('Їжа', 'expense', Decimal('320'), 'Кафе', 4),
            ('Транспорт', 'expense', Decimal('400'), 'Метро', 6),
            ('Житло', 'expense', Decimal('7500'), 'Оренда', 1),
            ('Розваги', 'expense', Decimal('600'), 'Кіно', 8),
            ('Їжа', 'expense', Decimal('1200'), 'Супермаркет', 10),
            ('Транспорт', 'expense', Decimal('250'), 'Таксі', 12),
            ('Розваги', 'expense', Decimal('900'), 'Концерт', 14),
            ('Їжа', 'expense', Decimal('480'), 'Обід', 15),
            ('Фріланс', 'income', Decimal('2000'), 'Бонус', 16),
            ('Житло', 'expense', Decimal('900'), 'Комунальні', 17),
            ('Транспорт', 'expense', Decimal('150'), 'Автобус', 18),
            ('Їжа', 'expense', Decimal('700'), 'Ринок', 19),
            ('Розваги', 'expense', Decimal('350'), 'Кава з друзями', 20),
            ('Їжа', 'expense', Decimal('540'), 'Доставка', 21),
            ('Транспорт', 'expense', Decimal('300'), 'Бензин', 22),
            ('Житло', 'expense', Decimal('200'), 'Інтернет', 23),
            ('Розваги', 'expense', Decimal('1100'), 'Підписки', 24),
        ]
        for i, (cat_name, tx_type, amount, note, day_offset) in enumerate(samples):
            day = min(month_start.day + day_offset, 28)
            occurred = month_start.replace(day=day)
            if occurred > today:
                occurred = today - timedelta(days=i % 10)
            tx = Transaction.objects.create(
                owner=demo,
                category=cats[cat_name],
                amount=amount,
                tx_type=tx_type,
                note=note,
                occurred_at=occurred,
            )
            tx.tags.add(tags[i % len(tags)])

        for name, limit in [('Їжа', Decimal('4000')), ('Транспорт', Decimal('1500')), ('Розваги', Decimal('2500'))]:
            Budget.objects.create(
                owner=demo,
                category=cats[name],
                amount=limit,
                month=month_start,
            )

        SavingsGoal.objects.create(
            owner=demo,
            title='Подушка безпеки',
            description='3 місяці витрат',
            target_amount=Decimal('50000'),
            saved_amount=Decimal('12000'),
            deadline=today + timedelta(days=180),
        )
        SavingsGoal.objects.create(
            owner=demo,
            title='Новий ноутбук',
            target_amount=Decimal('35000'),
            saved_amount=Decimal('8000'),
            deadline=today + timedelta(days=90),
        )

        self.stdout.write(self.style.SUCCESS(
            'Готово. Користувачі: demo / demo12345 та analyst / analyst12345'
        ))
