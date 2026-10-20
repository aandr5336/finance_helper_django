from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .currency import get_user_display_currency
from .forms import (
    BudgetForm,
    CategoryForm,
    GoalDepositForm,
    SavingsGoalForm,
    TagForm,
    TransactionFilterForm,
    TransactionForm,
)
from .models import Budget, Category, SavingsGoal, Tag, Transaction


class CurrencyFormKwargsMixin:
    """Передає поточну валюту відображення у форму (для введення сум)."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['currency'] = get_user_display_currency(self.request.user)
        return kwargs


class OwnerQuerysetMixin(LoginRequiredMixin):
    """Повертає лише об'єкти поточного користувача (analyst з правом бачить усі)."""

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.has_perm('budgeting.can_view_all_transactions') and self.model is Transaction:
            return qs.select_related('category', 'owner').prefetch_related('tags')
        return qs.filter(owner=user)


class OwnerEditMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return obj.owner_id == self.request.user.id


def home(request):
    """Коренева сторінка: лендінг для гостей, дашборд для авторизованих."""
    if request.user.is_authenticated:
        return redirect('budgeting:dashboard')
    return render(request, 'budgeting/landing.html')


# --- Dashboard (FBV): зручно зібрати кілька агрегатів без окремого CBV ---
@login_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)
    txs = Transaction.objects.filter(owner=request.user, occurred_at__gte=month_start)
    aggregates = txs.aggregate(
        income=Sum('amount', filter=Q(tx_type=Transaction.TxType.INCOME)),
        expenses=Sum('amount', filter=Q(tx_type=Transaction.TxType.EXPENSE)),
    )
    income = aggregates['income'] or Decimal('0')
    expenses = aggregates['expenses'] or Decimal('0')
    balance = income - expenses
    savings_rate = float(balance / income * 100) if income else 0.0

    by_category = (
        txs.filter(tx_type=Transaction.TxType.EXPENSE)
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')[:8]
    )
    recent = (
        Transaction.objects.filter(owner=request.user)
        .select_related('category')
        .prefetch_related('tags')[:8]
    )
    budgets = list(
        Budget.objects.filter(owner=request.user, month=month_start, is_active=True)
        .select_related('category')
    )
    spent_map = {
        row['category_id']: row['total'] or Decimal('0')
        for row in Transaction.objects.filter(
            owner=request.user,
            tx_type=Transaction.TxType.EXPENSE,
            occurred_at__year=month_start.year,
            occurred_at__month=month_start.month,
        ).values('category_id').annotate(total=Sum('amount'))
    }
    for budget in budgets:
        budget._spent_cache = spent_map.get(budget.category_id, Decimal('0'))
    goals = SavingsGoal.objects.filter(owner=request.user, is_done=False)[:5]

    from .product_views import build_onboarding

    return render(request, 'budgeting/dashboard.html', {
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'savings_rate': savings_rate,
        'by_category': by_category,
        'recent': recent,
        'budgets': budgets,
        'goals': goals,
        'month_label': month_start.strftime('%Y-%m'),
        'onboarding': build_onboarding(request.user),
    })


# --- Transactions CRUD ---
class TransactionListView(OwnerQuerysetMixin, ListView):
    model = Transaction
    paginate_by = 10
    template_name = 'budgeting/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'owner').prefetch_related('tags')
        self.filter_form = TransactionFilterForm(
            self.request.GET or None,
            user=self.request.user,
        )
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get('q'):
                qs = qs.filter(
                    Q(note__icontains=data['q']) | Q(category__name__icontains=data['q'])
                )
            if data.get('tx_type'):
                qs = qs.filter(tx_type=data['tx_type'])
            if data.get('date_from'):
                qs = qs.filter(occurred_at__gte=data['date_from'])
            if data.get('date_to'):
                qs = qs.filter(occurred_at__lte=data['date_to'])
            if data.get('category'):
                qs = qs.filter(category=data['category'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = getattr(self, 'filter_form', TransactionFilterForm(user=self.request.user))
        return ctx


class TransactionDetailView(OwnerQuerysetMixin, DetailView):
    model = Transaction
    template_name = 'budgeting/transaction_detail.html'
    context_object_name = 'transaction'

    def get_queryset(self):
        return super().get_queryset().select_related('category', 'owner').prefetch_related('tags')


class TransactionCreateView(CurrencyFormKwargsMixin, LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'budgeting/transaction_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Транзакцію створено.')
        return super().form_valid(form)


class TransactionUpdateView(CurrencyFormKwargsMixin, LoginRequiredMixin, OwnerEditMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'budgeting/transaction_form.html'

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Транзакцію оновлено.')
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, OwnerEditMixin, DeleteView):
    model = Transaction
    template_name = 'budgeting/transaction_confirm_delete.html'
    success_url = reverse_lazy('budgeting:transaction_list')

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Транзакцію видалено.')
        return super().form_valid(form)


# --- Categories ---
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'budgeting/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags'] = Tag.objects.filter(owner=self.request.user).order_by('name')
        ctx['tag_form'] = TagForm(user=self.request.user)
        return ctx


@login_required
def tag_create(request):
    if request.method != 'POST':
        return redirect('budgeting:category_list')
    form = TagForm(request.POST, user=request.user)
    if form.is_valid():
        tag = form.save(commit=False)
        tag.owner = request.user
        try:
            tag.save()
            messages.success(request, f'Тег «{tag.name}» додано.')
        except IntegrityError:
            messages.error(request, 'Такий тег уже існує.')
    else:
        for err in form.errors.get('name', form.non_field_errors()):
            messages.error(request, err)
    return redirect('budgeting:category_list')


@login_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = tag.name
        tag.delete()
        messages.success(request, f'Тег «{name}» видалено.')
    return redirect('budgeting:category_list')


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'budgeting/category_detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['transactions'] = (
            self.object.transactions.select_related('category')[:20]
        )
        return ctx


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'budgeting/category_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Категорію створено.')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, OwnerEditMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'budgeting/category_form.html'

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Категорію оновлено.')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, OwnerEditMixin, DeleteView):
    model = Category
    template_name = 'budgeting/category_confirm_delete.html'
    success_url = reverse_lazy('budgeting:category_list')

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                'Неможливо видалити категорію: є пов’язані транзакції.',
            )
            return redirect(self.object.get_absolute_url())


# --- Budgets ---
class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budgeting/budget_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user).select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        budgets = list(ctx['budgets'])
        if budgets:
            owner = self.request.user
            spent_rows = (
                Transaction.objects.filter(owner=owner, tx_type=Transaction.TxType.EXPENSE)
                .values('category_id', 'occurred_at__year', 'occurred_at__month')
                .annotate(total=Sum('amount'))
            )
            spent_map = {
                (r['category_id'], r['occurred_at__year'], r['occurred_at__month']): r['total'] or Decimal('0')
                for r in spent_rows
            }
            for budget in budgets:
                key = (budget.category_id, budget.month.year, budget.month.month)
                budget._spent_cache = spent_map.get(key, Decimal('0'))
            ctx['budgets'] = budgets
        return ctx


class BudgetDetailView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budgeting/budget_detail.html'
    context_object_name = 'budget'

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user).select_related('category')


class BudgetCreateView(CurrencyFormKwargsMixin, LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgeting/budget_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        month = form.cleaned_data['month']
        category = form.cleaned_data['category']
        amount = form.cleaned_data['amount']  # уже в гривнях
        existing = Budget.objects.filter(
            owner=self.request.user,
            category=category,
            month=month,
        ).first()
        if existing:
            existing.amount += amount
            if form.cleaned_data.get('is_active') is not None:
                existing.is_active = form.cleaned_data['is_active']
            existing.save(update_fields=['amount', 'is_active'])
            messages.success(
                self.request,
                f'Бюджет «{category.name}» збільшено на вказану суму.',
            )
            return redirect(existing.get_absolute_url())
        try:
            messages.success(self.request, 'Бюджет збережено.')
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, 'Бюджет для цієї категорії і місяця вже існує.')
            return self.form_invalid(form)


class BudgetUpdateView(CurrencyFormKwargsMixin, LoginRequiredMixin, OwnerEditMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgeting/budget_form.html'

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Бюджет оновлено.')
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, 'Бюджет для цієї категорії і місяця вже існує.')
            return self.form_invalid(form)


class BudgetDeleteView(LoginRequiredMixin, OwnerEditMixin, DeleteView):
    model = Budget
    template_name = 'budgeting/budget_confirm_delete.html'
    success_url = reverse_lazy('budgeting:budget_list')

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user)


# --- Goals ---
class GoalListView(LoginRequiredMixin, ListView):
    model = SavingsGoal
    template_name = 'budgeting/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        return SavingsGoal.objects.filter(owner=self.request.user)


class GoalDetailView(LoginRequiredMixin, DetailView):
    model = SavingsGoal
    template_name = 'budgeting/goal_detail.html'
    context_object_name = 'goal'

    def get_queryset(self):
        return SavingsGoal.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['deposit_form'] = GoalDepositForm(
            currency=get_user_display_currency(self.request.user)
        )
        return ctx


class GoalCreateView(CurrencyFormKwargsMixin, LoginRequiredMixin, CreateView):
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = 'budgeting/goal_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Ціль створено.')
        return super().form_valid(form)


class GoalUpdateView(CurrencyFormKwargsMixin, LoginRequiredMixin, OwnerEditMixin, UpdateView):
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = 'budgeting/goal_form.html'

    def get_queryset(self):
        return SavingsGoal.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Ціль оновлено.')
        return super().form_valid(form)


class GoalDeleteView(LoginRequiredMixin, OwnerEditMixin, DeleteView):
    model = SavingsGoal
    template_name = 'budgeting/goal_confirm_delete.html'
    success_url = reverse_lazy('budgeting:goal_list')

    def get_queryset(self):
        return SavingsGoal.objects.filter(owner=self.request.user)


@login_required
def goal_deposit(request, pk):
    """FBV POST-дія: поповнення цілі накопичення."""
    goal = get_object_or_404(SavingsGoal, pk=pk, owner=request.user)
    if request.method != 'POST':
        return redirect(goal.get_absolute_url())
    form = GoalDepositForm(
        request.POST,
        currency=get_user_display_currency(request.user),
    )
    if form.is_valid():
        amount = form.cleaned_data['amount']  # уже в гривнях
        goal.saved_amount += amount
        if goal.saved_amount >= goal.target_amount:
            goal.is_done = True
            messages.success(request, 'Ціль досягнуто!')
        else:
            messages.success(request, f'Поповнено на ₴{amount}.')
        goal.save(update_fields=['saved_amount', 'is_done'])
    else:
        messages.error(request, 'Некоректна сума поповнення.')
    return redirect(goal.get_absolute_url())


@login_required
@permission_required('budgeting.can_view_all_transactions', raise_exception=True)
def system_overview(request):
    """Сторінка лише для ролі analyst (перевірка permission на сервері)."""
    stats = {
        'users_with_tx': Transaction.objects.values('owner').distinct().count(),
        'total_transactions': Transaction.objects.count(),
        'total_expense': Transaction.objects.filter(
            tx_type=Transaction.TxType.EXPENSE
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0'),
        'total_income': Transaction.objects.filter(
            tx_type=Transaction.TxType.INCOME
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0'),
        'active_goals': SavingsGoal.objects.filter(is_done=False).count(),
    }
    latest = Transaction.objects.select_related('owner', 'category').order_by('-occurred_at')[:15]
    return render(request, 'budgeting/system_overview.html', {
        'stats': stats,
        'latest': latest,
    })
