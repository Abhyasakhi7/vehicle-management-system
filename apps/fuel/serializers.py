from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from apps.vehicles.models import Vehicle

from .models import FuelLog


class FuelLogSerializer(serializers.ModelSerializer):
    mileage = serializers.IntegerField(min_value=0)
    liters = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal("0.01")
    )
    price_per_liter = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0")
    )
    total_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = FuelLog
        fields = (
            "id",
            "vehicle",
            "date",
            "mileage",
            "liters",
            "price_per_liter",
            "total_cost",
            "is_full_tank",
            "station_name",
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

    @staticmethod
    def _calculate_total_cost(liters, price_per_liter):
        return (liters * price_per_liter).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def create(self, validated_data):
        validated_data["total_cost"] = self._calculate_total_cost(
            validated_data["liters"], validated_data["price_per_liter"]
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        liters = validated_data.get("liters", instance.liters)
        price_per_liter = validated_data.get(
            "price_per_liter", instance.price_per_liter
        )
        validated_data["total_cost"] = self._calculate_total_cost(
            liters, price_per_liter
        )
        return super().update(instance, validated_data)
