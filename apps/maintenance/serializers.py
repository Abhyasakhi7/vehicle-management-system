from decimal import Decimal

from rest_framework import serializers

from apps.vehicles.models import Vehicle

from .models import MaintenanceRecord


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    mileage = serializers.IntegerField(min_value=0)
    cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0")
    )

    class Meta:
        model = MaintenanceRecord
        fields = (
            "id",
            "vehicle",
            "service_type",
            "description",
            "service_date",
            "mileage",
            "cost",
            "workshop_name",
            "next_service_date",
            "next_service_mileage",
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

    def validate(self, attrs):
        instance = self.instance
        service_date = attrs.get(
            "service_date", instance.service_date if instance else None
        )
        next_service_date = attrs.get(
            "next_service_date", instance.next_service_date if instance else None
        )
        if next_service_date and service_date and next_service_date < service_date:
            raise serializers.ValidationError(
                {"next_service_date": "Next service date cannot be before service date."}
            )

        mileage = attrs.get("mileage", instance.mileage if instance else None)
        next_service_mileage = attrs.get(
            "next_service_mileage", instance.next_service_mileage if instance else None
        )
        if (
            next_service_mileage is not None
            and mileage is not None
            and next_service_mileage < mileage
        ):
            raise serializers.ValidationError(
                {
                    "next_service_mileage": (
                        "Next service mileage cannot be less than current mileage."
                    )
                }
            )
        return attrs
