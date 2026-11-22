from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import BudgetForm, CategoryForm, RegisterForm, TransactionForm
from .models import Budget, Category, Transaction


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        # Starter categories so the app is usable immediately
        for name in ["Food", "Rent", "Transport", "Shopping", "Bills", "Salary"]:
            Category.objects.create(user=user, name=name)
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


def add_months(d, n):
    """Return the first day of the month n months from d."""
    total = d.year * 12 + (d.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)


@login_required
def dashboard(request):
    today = date.today()
    try:
        year, month = map(int, request.GET.get("month", "").split("-"))
        first = date(year, month, 1)
    except ValueError:
        first = today.replace(day=1)
    next_first = add_months(first, 1)

    qs = Transaction.objects.filter(user=request.user, date__gte=first, date__lt=next_first)
    income = qs.filter(type="income").aggregate(t=Sum("amount"))["t"] or Decimal("0")
    expense = qs.filter(type="expense").aggregate(t=Sum("amount"))["t"] or Decimal("0")

    by_cat = list(
        qs.filter(type="expense")
        .values("category_id", "category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    spent_by_cat = {row["category_id"]: row["total"] for row in by_cat}

    budgets = []
    for b in Budget.objects.filter(user=request.user).select_related("category"):
        spent = spent_by_cat.get(b.category_id, Decimal("0"))
        budgets.append({
            "category": b.category.name,
            "limit": b.monthly_limit,
            "spent": spent,
            "percent": min(int(spent / b.monthly_limit * 100), 100),
            "over": spent > b.monthly_limit,
        })

    # Last 6 months income vs expense
    months = [add_months(first, -i) for i in range(5, -1, -1)]
    rows = (
        Transaction.objects.filter(user=request.user, date__gte=months[0], date__lt=next_first)
        .annotate(m=TruncMonth("date"))
        .values("m", "type")
        .annotate(t=Sum("amount"))
    )
    trend = {(r["m"], r["type"]): float(r["t"]) for r in rows}
    chart = {
        "pie_labels": [r["category__name"] or "Uncategorized" for r in by_cat],
        "pie_values": [float(r["total"]) for r in by_cat],
        "bar_labels": [m.strftime("%b %Y") for m in months],
        "bar_income": [trend.get((m, "income"), 0) for m in months],
        "bar_expense": [trend.get((m, "expense"), 0) for m in months],
    }

    return render(request, "tracker/dashboard.html", {
        "month_label": first.strftime("%B %Y"),
        "month_value": first.strftime("%Y-%m"),
        "prev_month": add_months(first, -1).strftime("%Y-%m"),
        "next_month": next_first.strftime("%Y-%m"),
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "budgets": budgets,
        "recent": qs[:5],
        "chart": chart,
    })


class OwnedQuerysetMixin(LoginRequiredMixin):
    """Users only ever see/edit their own rows."""

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class FormMixin(LoginRequiredMixin):
    template_name = "tracker/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.title
        return ctx


# ---- Transactions
class TransactionList(OwnedQuerysetMixin, ListView):
    model = Transaction
    paginate_by = 15
    template_name = "tracker/transaction_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("category")
        t = self.request.GET.get("type")
        c = self.request.GET.get("category")
        if t in ("income", "expense"):
            qs = qs.filter(type=t)
        if c and c.isdigit():
            qs = qs.filter(category_id=c)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.filter(user=self.request.user)
        return ctx


class TransactionCreate(FormMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    success_url = reverse_lazy("transactions")
    title = "Add transaction"


class TransactionUpdate(OwnedQuerysetMixin, FormMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    success_url = reverse_lazy("transactions")
    title = "Edit transaction"


class TransactionDelete(OwnedQuerysetMixin, DeleteView):
    model = Transaction
    success_url = reverse_lazy("transactions")
    template_name = "tracker/confirm_delete.html"


# ---- Categories
class CategoryList(OwnedQuerysetMixin, ListView):
    model = Category
    template_name = "tracker/category_list.html"


class CategoryCreate(FormMixin, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("categories")
    title = "Add category"


class CategoryDelete(OwnedQuerysetMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("categories")
    template_name = "tracker/confirm_delete.html"


# ---- Budgets
class BudgetList(OwnedQuerysetMixin, ListView):
    model = Budget
    template_name = "tracker/budget_list.html"


class BudgetCreate(FormMixin, CreateView):
    """Creates a budget, or updates the limit if the category already has one."""
    model = Budget
    form_class = BudgetForm
    success_url = reverse_lazy("budgets")
    title = "Set budget"

    def form_valid(self, form):
        Budget.objects.update_or_create(
            user=self.request.user,
            category=form.cleaned_data["category"],
            defaults={"monthly_limit": form.cleaned_data["monthly_limit"]},
        )
        return redirect(self.success_url)


class BudgetDelete(OwnedQuerysetMixin, DeleteView):
    model = Budget
    success_url = reverse_lazy("budgets")
    template_name = "tracker/confirm_delete.html"
