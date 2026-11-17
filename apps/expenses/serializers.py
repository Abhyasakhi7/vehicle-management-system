from decimal import Decimal

from rest_framework import serializers

from apps.vehicles.models import Vehicle

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0")
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "vehicle",
            "category",
            "description",
            "amount",
            "date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            self.fields["vehicle"].queryset = Vehicle.objects.filter(owner=request.user)
        else:
            self.fields["vehicle"].queryset = Vehicle.objects.none()
