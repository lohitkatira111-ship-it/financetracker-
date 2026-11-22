from django.urls import path
from . import views as v

urlpatterns = [
    path("", v.dashboard, name="dashboard"),
    path("register/", v.register, name="register"),

    path("transactions/", v.TransactionList.as_view(), name="transactions"),
    path("transactions/add/", v.TransactionCreate.as_view(), name="transaction_add"),
    path("transactions/<int:pk>/edit/", v.TransactionUpdate.as_view(), name="transaction_edit"),
    path("transactions/<int:pk>/delete/", v.TransactionDelete.as_view(), name="transaction_delete"),

    path("categories/", v.CategoryList.as_view(), name="categories"),
    path("categories/add/", v.CategoryCreate.as_view(), name="category_add"),
    path("categories/<int:pk>/delete/", v.CategoryDelete.as_view(), name="category_delete"),

    path("budgets/", v.BudgetList.as_view(), name="budgets"),
    path("budgets/add/", v.BudgetCreate.as_view(), name="budget_add"),
    path("budgets/<int:pk>/delete/", v.BudgetDelete.as_view(), name="budget_delete"),
]
