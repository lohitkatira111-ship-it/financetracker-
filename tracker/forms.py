from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Budget, Category, Transaction


class UserScopedForm(forms.ModelForm):
    """Limits the category dropdown to the logged-in user's categories."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if "category" in self.fields:
            self.fields["category"].queryset = Category.objects.filter(user=user)


class TransactionForm(UserScopedForm):
    class Meta:
        model = Transaction
        fields = ["type", "amount", "category", "date", "note"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class CategoryForm(UserScopedForm):
    class Meta:
        model = Category
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if Category.objects.filter(user=self.user, name__iexact=name).exists():
            raise forms.ValidationError("You already have this category.")
        return name


class BudgetForm(UserScopedForm):
    class Meta:
        model = Budget
        fields = ["category", "monthly_limit"]

    def clean_monthly_limit(self):
        limit = self.cleaned_data["monthly_limit"]
        if limit <= 0:
            raise forms.ValidationError("Limit must be greater than zero.")
        return limit


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username"]
