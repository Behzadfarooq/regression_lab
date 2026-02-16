from django.db.models import Count, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Order, OrderItem
from .serializers import CustomerSerializer, OrderSerializer, OrderItemSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-id")
    serializer_class = CustomerSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("customer").prefetch_related("items")
        # Default behavior: hide archived orders in list views.
        # (Note: detail views should still retrieve by id.)
        if self.action == "list":
            qs = qs.filter(is_archived=False)

            status_value = (self.request.query_params.get("status") or "").strip()
            email_value = (self.request.query_params.get("email") or "").strip()

            if status_value:
                allowed_statuses = {choice for choice, _ in Order.Status.choices}
                if status_value not in allowed_statuses:
                    allowed_text = ", ".join(sorted(allowed_statuses))
                    raise ValidationError({"status": f"Invalid status. Use one of: {allowed_text}."})
                qs = qs.filter(status=status_value)

            if email_value:
                qs = qs.filter(customer__email__icontains=email_value)

        return qs

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response({"id": order.id, "status": order.status})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        order = self.get_object()
        order.is_archived = True
        order.save(update_fields=["is_archived", "updated_at"])
        return Response({"id": order.id, "is_archived": order.is_archived})

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by("-id")
    serializer_class = OrderItemSerializer

class OrdersSummaryView(APIView):
    """Intentionally slow summary endpoint.

    Returns top customers by total spent (paid orders only).
    This is written in a purposely inefficient way to give candidates a perf target.
    """

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))

        paid_filter = Q(orders__status=Order.Status.PAID, orders__is_archived=False)
        customer_rows = (
            Customer.objects.filter(is_active=True)
            .annotate(
                order_count=Count("orders", filter=paid_filter),
                total_cents=Coalesce(
                    Sum("orders__total_cents", filter=paid_filter),
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
            .order_by("-total_cents", "-id")[:limit]
            .values("id", "email", "order_count", "total_cents")
        )

        rows = [
            {
                "customer_id": row["id"],
                "email": row["email"],
                "order_count": row["order_count"],
                "total_cents": row["total_cents"],
            }
            for row in customer_rows
        ]

        return Response({"limit": limit, "rows": rows})
