from django.contrib import admin

from .models import FuelLog


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle",
        "date",
        "mileage",
        "liters",
        "price_per_liter",
        "total_cost",
        "is_full_tank",
    )
    list_filter = ("is_full_tank", "date")
    search_fields = ("vehicle__name", "vehicle__plate_number", "station_name")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
