from django.contrib import admin

from .models import Budget, Category, SavingsGoal, Tag, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'owner', 'is_active', 'created_at')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'owner__username')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'category', 'amount', 'tx_type', 'occurred_at')
    list_filter = ('tx_type', 'occurred_at')
    search_fields = ('note', 'category__name', 'owner__username')
    autocomplete_fields = ('category', 'owner', 'tags')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'month', 'owner', 'is_active')
    list_filter = ('is_active', 'month')
    search_fields = ('category__name', 'owner__username')


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_amount', 'saved_amount', 'is_done', 'owner')
    list_filter = ('is_done',)
    search_fields = ('title', 'owner__username')
