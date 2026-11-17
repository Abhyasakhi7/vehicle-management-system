from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import FuelLog
from .serializers import FuelLogSerializer


class FuelLogViewSet(viewsets.ModelViewSet):
    serializer_class = FuelLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle", "is_full_tank", "date"]
    search_fields = [
        "station_name",
        "vehicle__name",
        "vehicle__plate_number",
    ]
    ordering_fields = ["date", "mileage", "total_cost", "created_at"]
    ordering = ["-date", "-id"]

    def get_queryset(self):
        return FuelLog.objects.filter(vehicle__owner=self.request.user).select_related(
            "vehicle"
        )
