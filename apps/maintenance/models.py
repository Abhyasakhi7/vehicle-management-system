from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.vehicles.models import Vehicle


class MaintenanceRecord(models.Model):
    class ServiceType(models.TextChoices):
        OIL_CHANGE = "OIL_CHANGE", "Oil Change"
        TIRE = "TIRE", "Tire Replacement"
        BRAKES = "BRAKES", "Brake Service"
        BATTERY = "BATTERY", "Battery"
        GENERAL_SERVICE = "GENERAL_SERVICE", "General Service"
        REPAIR = "REPAIR", "Repair"
        OTHER = "OTHER", "Other"

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="maintenance_records",
    )
    service_type = models.CharField(
        max_length=30,
        choices=ServiceType.choices,
        default=ServiceType.GENERAL_SERVICE,
    )
    description = models.TextField(blank=True)
    service_date = models.DateField()
    mileage = models.PositiveIntegerField()
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    workshop_name = models.CharField(max_length=120, blank=True)
    next_service_date = models.DateField(null=True, blank=True)
    next_service_mileage = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-service_date", "-id"]
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"

    def clean(self):
        super().clean()
        if self.next_service_date and self.next_service_date < self.service_date:
            raise ValidationError(
                {"next_service_date": "Next service date cannot be before service date."}
            )
        if self.next_service_mileage is not None and self.next_service_mileage < self.mileage:
            raise ValidationError(
                {"next_service_mileage": "Next service mileage cannot be less than current mileage."}
            )

    def __str__(self):
        return f"{self.vehicle} - {self.get_service_type_display()} ({self.service_date})"
