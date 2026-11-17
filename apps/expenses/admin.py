from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "category", "description", "amount", "date")
    list_filter = ("category", "date")
    search_fields = ("vehicle__name", "vehicle__plate_number", "description")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
