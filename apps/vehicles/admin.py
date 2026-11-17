from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "model",
        "year",
        "plate_number",
        "vehicle_type",
        "fuel_type",
        "mileage",
        "owner",
    )
    list_filter = ("vehicle_type", "fuel_type", "transmission")
    search_fields = ("name", "brand", "model", "plate_number")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("owner",)
