from datetime import date

from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    year = serializers.IntegerField(min_value=1900, max_value=date.today().year + 1)

    class Meta:
        model = Vehicle
        fields = (
            "id",
            "owner",
            "name",
            "brand",
            "model",
            "year",
            "vehicle_type",
            "plate_number",
            "fuel_type",
            "transmission",
            "mileage",
            "color",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")
