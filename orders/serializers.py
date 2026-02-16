from rest_framework import serializers
from .models import Customer, Order, OrderItem

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "is_active", "created_at"]

class OrderItemSerializer(serializers.ModelSerializer):
    line_total_cents = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "order", "sku", "quantity", "unit_price_cents", "line_total_cents"]

    def get_line_total_cents(self, obj: OrderItem) -> int:
        return obj.line_total_cents()

class OrderSerializer(serializers.ModelSerializer):
    # NOTE: This nested view can be made more efficient with prefetch_related.
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "customer", "customer_email", "status",
            "total_cents", "is_archived", "created_at", "updated_at",
            "items",
        ]

    def get_customer_email(self, obj: Order) -> str:
        # This triggers a DB fetch unless select_related("customer") is used.
        return obj.customer.email
