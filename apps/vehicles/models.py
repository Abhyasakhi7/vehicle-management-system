from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Vehicle(models.Model):
    class VehicleType(models.TextChoices):
        CAR = "CAR", "Car"
        MOTORCYCLE = "MOTORCYCLE", "Motorcycle"
        OTHER = "OTHER", "Other"

    class FuelType(models.TextChoices):
        PETROL = "PETROL", "Petrol"
        DIESEL = "DIESEL", "Diesel"
        ELECTRIC = "ELECTRIC", "Electric"
        HYBRID = "HYBRID", "Hybrid"

    class Transmission(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        AUTOMATIC = "AUTOMATIC", "Automatic"
        CVT = "CVT", "CVT"
        OTHER = "OTHER", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=60)
    model = models.CharField(max_length=60)
    year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(date.today().year + 1),
        ]
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
        default=VehicleType.CAR,
    )
    plate_number = models.CharField(max_length=20, unique=True)
    fuel_type = models.CharField(max_length=20, choices=FuelType.choices)
    transmission = models.CharField(
        max_length=20,
        choices=Transmission.choices,
        default=Transmission.MANUAL,
    )
    mileage = models.PositiveIntegerField(default=0, help_text="Odometer in km")
    color = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def __str__(self):
        return f"{self.name} ({self.plate_number})"
