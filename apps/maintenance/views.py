from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import MaintenanceRecord
from .serializers import MaintenanceRecordSerializer


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle", "service_type", "service_date"]
    search_fields = [
        "description",
        "workshop_name",
        "vehicle__name",
        "vehicle__plate_number",
    ]
    ordering_fields = ["service_date", "cost", "mileage", "created_at"]
    ordering = ["-service_date", "-id"]

    def get_queryset(self):
        return MaintenanceRecord.objects.filter(
            vehicle__owner=self.request.user
        ).select_related("vehicle")
