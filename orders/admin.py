from django.contrib import admin
from .models import Customer, Order, OrderItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name", "is_active", "created_at")
    search_fields = ("email", "name")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total_cents", "is_archived", "created_at")
    list_filter = ("status", "is_archived")
    search_fields = ("customer__email",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "sku", "quantity", "unit_price_cents")
    search_fields = ("sku",)
