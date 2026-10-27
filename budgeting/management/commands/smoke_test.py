from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.test import Client, override_settings

from budgeting.models import Category, SavingsGoal, Transaction


class Command(BaseCommand):
    help = 'Smoke-test ключових маршрутів і POST-дій'

    def handle(self, *args, **options):
        with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
            self._run_checks()

    def _run_checks(self):
        c = Client()
        errors = []

        def check(cond, msg):
            if not cond:
                errors.append(msg)

        # Публічний лендінг (гость) — 200, не редірект
        r = c.get('/')
        check(r.status_code == 200, f'landing anon: {r.status_code}')
        check(c.get('/accounts/login/').status_code == 200, 'login page')
        check(c.get('/about/').status_code == 200, 'about')
        check(c.get('/faq/').status_code == 200, 'faq')
        check(c.get('/pricing/').status_code == 404, 'pricing removed')


        check(c.login(username='demo', password='demo12345'), 'login demo')

        # Авторизований / → dashboard
        r = c.get('/')
        check(r.status_code == 302, f'home auth redirect: {r.status_code}')

        for path in [
            '/dashboard/',
            '/transactions/',
            '/categories/',
            '/budgets/',
            '/goals/',
            '/reports/',
            '/insights/',
            '/help/',
            '/transactions/calendar/',
            '/transactions/add/',
            '/categories/add/',
            '/budgets/add/',
            '/goals/add/',
            '/accounts/settings/',
        ]:
            code = c.get(path).status_code
            check(code == 200, f'GET {path} -> {code}')

        tx = Transaction.objects.filter(owner__username='demo').first()
        if tx:
            code = c.get(f'/transactions/{tx.pk}/').status_code
            check(code == 200, f'tx detail -> {code}')
        else:
            errors.append('no demo transactions')

        code = c.get('/transactions/', {'q': 'їжа', 'tx_type': 'expense'}).status_code
        check(code == 200, f'filter -> {code}')

        cat = Category.objects.filter(owner__username='demo', category_type='expense').first()
        r = c.post(
            '/transactions/add/',
            {
                'category': cat.pk,
                'amount': '123.45',
                'tx_type': 'expense',
                'note': 'smoke test',
                'occurred_at': date.today().isoformat(),
            },
        )
        check(r.status_code == 302, f'create tx -> {r.status_code}')

        r = c.post(
            '/transactions/add/',
            {
                'category': cat.pk,
                'amount': '-5',
                'tx_type': 'expense',
                'note': 'bad',
                'occurred_at': date.today().isoformat(),
            },
        )
        check(r.status_code == 200, f'invalid amount -> {r.status_code}')

        goal = SavingsGoal.objects.filter(owner__username='demo', is_done=False).first()
        r = c.post(f'/goals/{goal.pk}/deposit/', {'amount': '50'})
        check(r.status_code == 302, f'deposit -> {r.status_code}')

        r = c.get('/overview/')
        check(r.status_code == 403, f'demo overview -> {r.status_code}')

        other, _ = User.objects.get_or_create(username='other_smoke')
        if not other.has_usable_password():
            other.set_password('x')
            other.save()
        alien_cat, _ = Category.objects.get_or_create(
            owner=other,
            name='Alien',
            category_type='expense',
            defaults={'icon': 'tag', 'color': '#888888'},
        )
        alien, _ = Transaction.objects.get_or_create(
            owner=other,
            category=alien_cat,
            note='alien smoke',
            defaults={
                'amount': '10.00',
                'tx_type': 'expense',
                'occurred_at': date.today(),
            },
        )
        check(c.get(f'/transactions/{alien.pk}/').status_code == 404, 'alien detail 404')
        check(c.get(f'/transactions/{alien.pk}/edit/').status_code == 404, 'alien edit 404')

        r = c.post(f'/categories/{cat.pk}/delete/')
        check(r.status_code in (200, 302), f'protected category delete -> {r.status_code}')
        check(Category.objects.filter(pk=cat.pk).exists(), 'category still exists after protect')

        c.logout()
        check(c.login(username='analyst', password='analyst12345'), 'analyst login')
        check(c.get('/overview/').status_code == 200, 'analyst overview')
        check(c.post('/accounts/logout/').status_code in (200, 302), 'logout POST')

        if errors:
            self.stdout.write(self.style.ERROR(f'FAIL ({len(errors)})'))
            for e in errors:
                self.stdout.write(f' - {e}')
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS('ALL_OK'))
