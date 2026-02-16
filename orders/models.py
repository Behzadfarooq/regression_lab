from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(Customer, related_name="orders", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_cents = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order #{self.id} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    sku = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField(default=1)
    unit_price_cents = models.PositiveIntegerField(default=0)

    def line_total_cents(self) -> int:
        return int(self.quantity) * int(self.unit_price_cents)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep order total in sync (simple, intentionally not the most efficient way).
        total = 0
        for item in self.order.items.all():
            total += item.line_total_cents()
        self.order.total_cents = total
        self.order.save(update_fields=["total_cents", "updated_at"])

    def __str__(self) -> str:
        return f"{self.sku} x{self.quantity}"
