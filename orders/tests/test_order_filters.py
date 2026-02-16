from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import Customer, Order


class OrderListFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = Customer.objects.create(name="Alice", email="alice@example.com")
        self.bob = Customer.objects.create(name="Bob", email="bob@example.com")

        self.alice_paid = Order.objects.create(customer=self.alice, status=Order.Status.PAID)
        self.alice_draft = Order.objects.create(customer=self.alice, status=Order.Status.DRAFT)
        self.bob_paid_archived = Order.objects.create(
            customer=self.bob,
            status=Order.Status.PAID,
            is_archived=True,
        )
        self.bob_shipped = Order.objects.create(customer=self.bob, status=Order.Status.SHIPPED)

    def test_filter_by_status_returns_only_matching_non_archived_orders(self):
        res = self.client.get("/api/orders/?status=paid")
        self.assertEqual(res.status_code, 200)

        rows = res.json()["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], self.alice_paid.id)
        self.assertEqual(rows[0]["status"], Order.Status.PAID)
        self.assertFalse(rows[0]["is_archived"])

    def test_filter_by_email_contains(self):
        res = self.client.get("/api/orders/?email=alice")
        self.assertEqual(res.status_code, 200)

        rows = res.json()["results"]
        returned_ids = {row["id"] for row in rows}

        self.assertEqual(returned_ids, {self.alice_paid.id, self.alice_draft.id})

    def test_filter_by_status_and_email(self):
        res = self.client.get("/api/orders/?status=paid&email=alice")
        self.assertEqual(res.status_code, 200)

        rows = res.json()["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], self.alice_paid.id)

    def test_filter_with_invalid_status_returns_400(self):
        res = self.client.get("/api/orders/?status=not-a-real-status")
        self.assertEqual(res.status_code, 400)
        self.assertIn("status", res.json())
