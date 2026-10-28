from datetime import date

from django import forms
from django.forms.models import ModelChoiceIteratorValue

from .currency import CURRENCY_SYMBOLS, convert_from_uah, convert_to_uah
from .defaults import ensure_default_categories
from .models import Budget, Category, SavingsGoal, Tag, Transaction
from .validators import validate_positive_amount

# HTML5 <input type="date"> завжди шле YYYY-MM-DD (незалежно від LANGUAGE_CODE)
_HTML5_DATE_FORMATS = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']


def _amount_label(base: str, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency == 'UAH':
        return base
    return f'{base} ({currency}, {symbol})'


class CurrencyAwareAmountMixin:
    """Приймає суму в валюті відображення, у cleaned_data кладе гривні."""

    amount_field_names = ('amount',)
    currency = 'UAH'

    def setup_currency(self, currency: str = 'UAH'):
        self.currency = (currency or 'UAH').upper()
        for name in self.amount_field_names:
            if name not in self.fields:
                continue
            field = self.fields[name]
            field.label = _amount_label(field.label or 'Сума', self.currency)
            if self.instance and getattr(self.instance, 'pk', None) and self.currency != 'UAH':
                raw = getattr(self.instance, name, None)
                if raw is not None:
                    self.initial[name] = convert_from_uah(raw, self.currency)

    def _convert_amount_fields(self, cleaned):
        for name in self.amount_field_names:
            if name in cleaned and cleaned[name] is not None:
                cleaned[name] = convert_to_uah(cleaned[name], self.currency)
        return cleaned


class CategoryTypeSelect(forms.Select):
    """Опції категорій з data-type для динамічного фільтра в JS."""

    def __init__(self, *args, type_map=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_map = type_map or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        raw = value
        if isinstance(value, ModelChoiceIteratorValue):
            raw = value.value
        key = str(raw) if raw not in (None, '') else ''
        if key and key in self.type_map:
            option['attrs']['data-type'] = self.type_map[key]
        return option


class TransactionForm(CurrencyAwareAmountMixin, forms.ModelForm):
    amount_field_names = ('amount',)
    new_tags = forms.CharField(
        label='Нові теги',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'наприклад: кава, робота (через кому)',
        }),
    )

    class Meta:
        model = Transaction
        fields = ['tx_type', 'category', 'amount', 'note', 'occurred_at', 'tags']
        widgets = {
            'occurred_at': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'},
            ),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tx_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_tx_type'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'fh-tag-list'}),
        }

    def __init__(self, *args, user=None, currency='UAH', **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['tx_type'].choices = list(Transaction.TxType.choices)
        if not (self.instance and self.instance.pk) and not self.is_bound:
            # одразу «витрата» — інакше JS-фільтр лишає користувача без зрозумілого списку
            self.fields['tx_type'].initial = Transaction.TxType.EXPENSE

        category_qs = Category.objects.none()
        tag_qs = Tag.objects.none()
        if user is not None:
            ensure_default_categories(user)
            category_qs = Category.objects.filter(owner=user, is_active=True).order_by(
                'category_type', 'name'
            )
            tag_qs = Tag.objects.filter(owner=user).order_by('name')

        type_map = {str(c.pk): c.category_type for c in category_qs}
        # для JS-фільтра в шаблоні (json_script)
        self.category_choices = [
            {'id': str(c.pk), 'name': c.name, 'type': c.category_type}
            for c in category_qs
        ]

        self.fields['category'].widget = CategoryTypeSelect(
            attrs={'class': 'form-select', 'id': 'id_category'},
            type_map=type_map,
        )
        self.fields['category'].empty_label = '— оберіть категорію —'
        self.fields['category'].queryset = category_qs

        self.fields['tags'].queryset = tag_qs
        self.fields['tags'].required = False
        self.fields['tags'].label = 'Теги'
        # порядок: спочатку існуючі, потім поле нових
        self.order_fields(
            ['tx_type', 'category', 'amount', 'note', 'occurred_at', 'tags', 'new_tags']
        )

        self.fields['amount'].validators.append(validate_positive_amount)
        self.fields['occurred_at'].required = False
        self.fields['occurred_at'].input_formats = _HTML5_DATE_FORMATS
        if not self.is_bound and not (self.instance and self.instance.pk):
            self.fields['occurred_at'].initial = date.today()
        elif not self.is_bound and self.instance and self.instance.pk:
            self.fields['occurred_at'].initial = self.instance.occurred_at
        self.setup_currency(currency)

    def clean_occurred_at(self):
        value = self.cleaned_data.get('occurred_at') or date.today()
        if value > date.today():
            raise forms.ValidationError('Дата операції не може бути в майбутньому.')
        return value

    def clean_new_tags(self):
        raw = self.cleaned_data.get('new_tags') or ''
        names = []
        for part in raw.replace(';', ',').split(','):
            name = part.strip()
            if name:
                names.append(name[:50])
        return names

    def clean(self):
        cleaned = super().clean()
        cleaned = self._convert_amount_fields(cleaned)
        category = cleaned.get('category')
        tx_type = cleaned.get('tx_type')
        if category and tx_type and category.category_type != tx_type:
            raise forms.ValidationError(
                'Тип категорії має збігатися з типом транзакції (дохід/витрата).'
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            self._attach_new_tags(instance)
        return instance

    def _attach_new_tags(self, instance):
        owner = instance.owner or self.user
        if owner is None:
            return
        for name in self.cleaned_data.get('new_tags') or []:
            tag, _ = Tag.objects.get_or_create(owner=owner, name=name)
            instance.tags.add(tag)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon', 'color', 'category_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва тегу',
                'maxlength': '50',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['name'].label = 'Новий тег'

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Вкажіть назву тегу.')
        name = name[:50]
        qs = Tag.objects.filter(owner=self.user, name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if self.user is not None and qs.exists():
            raise forms.ValidationError('Такий тег уже існує.')
        return name


class BudgetForm(CurrencyAwareAmountMixin, forms.ModelForm):
    amount_field_names = ('amount',)

    class Meta:
        model = Budget
        fields = ['category', 'amount', 'month', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'month': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'},
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, currency='UAH', **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            ensure_default_categories(user)
            self.fields['category'].queryset = Category.objects.filter(
                owner=user,
                category_type=Category.CategoryType.EXPENSE,
                is_active=True,
            )
        self.fields['category'].empty_label = '— оберіть категорію —'
        self.fields['amount'].validators.append(validate_positive_amount)
        self.fields['month'].required = False
        self.fields['month'].input_formats = _HTML5_DATE_FORMATS
        today = date.today()
        month_start = today.replace(day=1)
        if not self.is_bound and not (self.instance and self.instance.pk):
            self.fields['month'].initial = month_start
        elif not self.is_bound and self.instance and self.instance.pk:
            self.fields['month'].initial = self.instance.month
        self.setup_currency(currency)

    def clean_month(self):
        value = self.cleaned_data.get('month') or date.today().replace(day=1)
        return value.replace(day=1)

    def clean(self):
        cleaned = super().clean()
        return self._convert_amount_fields(cleaned)


class SavingsGoalForm(CurrencyAwareAmountMixin, forms.ModelForm):
    amount_field_names = ('target_amount',)

    class Meta:
        model = SavingsGoal
        fields = ['title', 'description', 'target_amount', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'deadline': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'},
            ),
        }

    def __init__(self, *args, currency='UAH', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_amount'].validators.append(validate_positive_amount)
        self.fields['deadline'].required = False
        self.fields['deadline'].input_formats = _HTML5_DATE_FORMATS
        if not self.is_bound and not (self.instance and self.instance.pk):
            self.fields['deadline'].initial = date.today()
        elif not self.is_bound and self.instance and self.instance.pk and self.instance.deadline:
            self.fields['deadline'].initial = self.instance.deadline
        self.setup_currency(currency)

    def clean_deadline(self):
        # якщо поле порожнє (не чіпали / стерли) — сьогодні
        return self.cleaned_data.get('deadline') or date.today()

    def clean(self):
        cleaned = super().clean()
        return self._convert_amount_fields(cleaned)


class TransactionFilterForm(forms.Form):
    """Непов'язана з моделлю форма пошуку/фільтрації транзакцій."""

    q = forms.CharField(
        label='Пошук',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Примітка або категорія…',
        }),
    )
    tx_type = forms.ChoiceField(
        label='Тип',
        required=False,
        choices=[('', 'Усі')] + list(Transaction.TxType.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        label='Від',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_to = forms.DateField(
        label='До',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    category = forms.ModelChoiceField(
        label='Категорія',
        required=False,
        queryset=Category.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['category'].queryset = Category.objects.filter(owner=user)
        self.fields['date_from'].input_formats = _HTML5_DATE_FORMATS
        self.fields['date_to'].input_formats = _HTML5_DATE_FORMATS

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Дата «від» не може бути пізніше за «до».')
        return cleaned


class GoalDepositForm(forms.Form):
    amount = forms.DecimalField(
        label='Сума поповнення',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )

    def __init__(self, *args, currency='UAH', **kwargs):
        super().__init__(*args, **kwargs)
        self.currency = (currency or 'UAH').upper()
        self.fields['amount'].validators.append(validate_positive_amount)
        self.fields['amount'].label = _amount_label('Сума поповнення', self.currency)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        return convert_to_uah(amount, self.currency)
