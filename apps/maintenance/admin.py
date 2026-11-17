from django.contrib import admin

from .models import MaintenanceRecord


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle",
        "service_type",
        "service_date",
        "mileage",
        "cost",
        "workshop_name",
    )
    list_filter = ("service_type", "service_date")
    search_fields = (
        "vehicle__name",
        "vehicle__plate_number",
        "workshop_name",
        "description",
    )
    date_hierarchy = "service_date"
    readonly_fields = ("created_at", "updated_at")
