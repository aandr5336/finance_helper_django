from django.urls import path

from . import product_views, views

app_name = 'budgeting'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('overview/', views.system_overview, name='system_overview'),

    path('reports/', product_views.reports_home, name='reports'),
    path('insights/', product_views.insights, name='insights'),
    path('help/', product_views.help_index, name='help_index'),
    path('help/<slug:slug>/', product_views.help_article, name='help_article'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/calendar/', product_views.transaction_calendar, name='transaction_calendar'),
    path('transactions/add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),

    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('tags/add/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),

    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('budgets/add/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('budgets/<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget_delete'),

    path('goals/', views.GoalListView.as_view(), name='goal_list'),
    path('goals/add/', views.GoalCreateView.as_view(), name='goal_create'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal_detail'),
    path('goals/<int:pk>/edit/', views.GoalUpdateView.as_view(), name='goal_update'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal_delete'),
    path('goals/<int:pk>/deposit/', views.goal_deposit, name='goal_deposit'),
]
