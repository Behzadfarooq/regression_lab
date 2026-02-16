from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.views import CustomerViewSet, OrderViewSet, OrderItemViewSet, OrdersSummaryView
from .views import DevSeedView

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"items", OrderItemViewSet, basename="items")

# IMPORTANT: put explicit routes BEFORE the router include.
# Otherwise `/api/orders/summary/` gets captured by the router as `orders/<pk>/` with pk="summary".
urlpatterns = [
    path("orders/summary/", OrdersSummaryView.as_view(), name="orders-summary"),
    path("dev/seed/", DevSeedView.as_view(), name="dev-seed"),
    path("", include(router.urls)),
]
