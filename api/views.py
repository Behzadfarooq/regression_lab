import random
import string

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from orders.models import Customer, Order, OrderItem

def _rand_email(i: int) -> str:
    return f"user{i}@example.com"

def _rand_name() -> str:
    return "User " + "".join(random.choices(string.ascii_uppercase, k=5))

class DevSeedView(APIView):
    """Dev-only seeding endpoint for the take-home repo.

    POST /api/dev/seed/ { customers, orders_per_customer, items_per_order }

    This is intentionally exposed to keep the take-home fast to run locally.
    """

    def post(self, request):
        customers = int(request.data.get("customers", 100))
        orders_per_customer = int(request.data.get("orders_per_customer", 5))
        items_per_order = int(request.data.get("items_per_order", 3))

        created_customers = 0
        created_orders = 0
        created_items = 0

        last_id = Customer.objects.order_by('-id').values_list('id', flat=True).first() or 0
        start_idx = int(last_id) + 1

        status_values = [Order.Status.PAID, Order.Status.DRAFT, Order.Status.SHIPPED]
        status_weights = [0.55, 0.35, 0.10]
        price_values = [199, 499, 999, 1499, 2499]

        with transaction.atomic():
            for i in range(start_idx, start_idx + customers):
                c = Customer.objects.create(
                    name=_rand_name(),
                    email=_rand_email(i),
                    is_active=True,
                )
                created_customers += 1

                for _ in range(orders_per_customer):
                    status_choice = random.choices(status_values, weights=status_weights)[0]

                    item_specs = []
                    order_total_cents = 0
                    for _ in range(items_per_order):
                        sku = f"SKU-{random.randint(1, 200)}"
                        qty = random.randint(1, 5)
                        price = random.choice(price_values)
                        order_total_cents += qty * price
                        item_specs.append((sku, qty, price))

                    o = Order.objects.create(
                        customer=c,
                        status=status_choice,
                        total_cents=order_total_cents,
                    )
                    created_orders += 1

                    item_rows = [
                        OrderItem(order=o, sku=sku, quantity=qty, unit_price_cents=price)
                        for sku, qty, price in item_specs
                    ]
                    OrderItem.objects.bulk_create(item_rows)
                    created_items += len(item_rows)

        return Response({
            "customers": created_customers,
            "orders": created_orders,
            "items": created_items,
        }, status=status.HTTP_201_CREATED)
