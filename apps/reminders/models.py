from django.core.exceptions import ValidationError
from django.db import models

from apps.vehicles.models import Vehicle


class Reminder(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    due_mileage = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Reminder"
        verbose_name_plural = "Reminders"

    def clean(self):
        super().clean()
        if self.due_date is None and self.due_mileage is None:
            raise ValidationError(
                "Set at least one of due date or due mileage for a reminder."
            )

    def __str__(self):
        return f"{self.vehicle} - {self.title}"
