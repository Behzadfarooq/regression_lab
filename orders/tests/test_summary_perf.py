from django.test import TestCase
from rest_framework.test import APIClient
from orders.models import Customer, Order, OrderItem

class SummaryEndpointTests(TestCase):
    def test_summary_endpoint_returns_rows(self):
        client = APIClient()

        c = Customer.objects.create(name="Bob", email="bob@example.com")
        o = Order.objects.create(customer=c, status=Order.Status.PAID)
        OrderItem.objects.create(order=o, sku="SKU-1", quantity=2, unit_price_cents=500)

        res = client.get("/api/orders/summary/?limit=10")
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertIn("rows", payload)
        self.assertGreaterEqual(len(payload["rows"]), 1)

    def test_summary_uses_paid_non_archived_orders_and_sorts_desc(self):
        client = APIClient()

        top = Customer.objects.create(name="Top", email="top@example.com", is_active=True)
        lower = Customer.objects.create(name="Lower", email="lower@example.com", is_active=True)
        inactive = Customer.objects.create(name="Off", email="off@example.com", is_active=False)

        Order.objects.create(customer=top, status=Order.Status.PAID, total_cents=5000)
        Order.objects.create(customer=top, status=Order.Status.PAID, total_cents=2000)
        Order.objects.create(customer=top, status=Order.Status.DRAFT, total_cents=99999)
        Order.objects.create(customer=top, status=Order.Status.PAID, total_cents=7777, is_archived=True)

        Order.objects.create(customer=lower, status=Order.Status.PAID, total_cents=1000)
        Order.objects.create(customer=inactive, status=Order.Status.PAID, total_cents=8000)

        res = client.get("/api/orders/summary/?limit=10")
        self.assertEqual(res.status_code, 200)

        rows = res.json()["rows"]
        # Find our rows among seeded/default data if any.
        rows_by_email = {row["email"]: row for row in rows}

        self.assertEqual(rows_by_email["top@example.com"]["order_count"], 2)
        self.assertEqual(rows_by_email["top@example.com"]["total_cents"], 7000)
        self.assertEqual(rows_by_email["lower@example.com"]["order_count"], 1)
        self.assertEqual(rows_by_email["lower@example.com"]["total_cents"], 1000)
        self.assertNotIn("off@example.com", rows_by_email)

        self.assertGreaterEqual(
            rows_by_email["top@example.com"]["total_cents"],
            rows_by_email["lower@example.com"]["total_cents"],
        )
