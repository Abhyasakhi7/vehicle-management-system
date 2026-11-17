from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle_type", "fuel_type", "transmission", "year", "brand"]
    search_fields = ["name", "brand", "model", "plate_number"]
    ordering_fields = ["name", "brand", "year", "mileage", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
