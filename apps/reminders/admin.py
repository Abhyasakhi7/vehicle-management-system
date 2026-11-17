from django.contrib import admin

from .models import Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "title", "due_date", "due_mileage", "status")
    list_filter = ("status", "due_date")
    search_fields = ("vehicle__name", "vehicle__plate_number", "title")
    readonly_fields = ("created_at", "updated_at")
