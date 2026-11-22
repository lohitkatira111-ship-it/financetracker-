from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Budget, Category, Transaction


class TrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("a", password="pw12345!x")
        self.other = User.objects.create_user("b", password="pw12345!x")
        self.cat = Category.objects.create(user=self.user, name="Food")
        self.client.login(username="a", password="pw12345!x")

    def test_login_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_register_creates_starter_categories(self):
        self.client.logout()
        self.client.post(reverse("register"), {"username": "new", "password1": "Str0ngPass!99", "password2": "Str0ngPass!99"})
        self.assertEqual(Category.objects.filter(user__username="new").count(), 6)

    def test_add_transaction_and_dashboard(self):
        r = self.client.post(reverse("transaction_add"), {
            "type": "expense", "amount": "250.50", "category": self.cat.id,
            "date": date.today().isoformat(), "note": "lunch"})
        self.assertEqual(r.status_code, 302)
        Transaction.objects.create(user=self.user, type="income", amount=1000, date=date.today())
        Budget.objects.create(user=self.user, category=self.cat, monthly_limit=200)
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["balance"], 1000 - 250.50)
        self.assertTrue(r.context["budgets"][0]["over"])

    def test_negative_amount_rejected(self):
        r = self.client.post(reverse("transaction_add"), {
            "type": "expense", "amount": "-5", "date": date.today().isoformat()})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_cannot_touch_other_users_data(self):
        t = Transaction.objects.create(user=self.other, type="expense", amount=5, date=date.today())
        self.assertEqual(self.client.get(reverse("transaction_edit", args=[t.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("transaction_delete", args=[t.pk])).status_code, 404)

    def test_budget_upsert_and_pages(self):
        for _ in range(2):
            self.client.post(reverse("budget_add"), {"category": self.cat.id, "monthly_limit": "500"})
        self.assertEqual(Budget.objects.count(), 1)
        for name in ["transactions", "categories", "budgets", "category_add"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard") + "?month=2026-01").status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard") + "?month=garbage").status_code, 200)
