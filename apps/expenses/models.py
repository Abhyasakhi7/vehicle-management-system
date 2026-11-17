from django.core.validators import MinValueValidator
from django.db import models

from apps.vehicles.models import Vehicle


class Expense(models.Model):
    class Category(models.TextChoices):
        TAX = "TAX", "Tax"
        INSURANCE = "INSURANCE", "Insurance"
        PARKING = "PARKING", "Parking"
        TOLL = "TOLL", "Toll"
        WASH = "WASH", "Wash"
        OTHER = "OTHER", "Other"

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"

    def __str__(self):
        return f"{self.vehicle} - {self.get_category_display()} ({self.amount})"
