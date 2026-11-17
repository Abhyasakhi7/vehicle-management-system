from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.vehicles.models import Vehicle


class FuelLog(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="fuel_logs",
    )
    date = models.DateField()
    mileage = models.PositiveIntegerField()
    liters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    price_per_liter = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_full_tank = models.BooleanField(default=False)
    station_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "Fuel Log"
        verbose_name_plural = "Fuel Logs"

    def __str__(self):
        return f"{self.vehicle} - {self.liters} L ({self.date})"
