from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Reminder
from .serializers import ReminderSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle", "status", "due_date"]
    search_fields = [
        "title",
        "description",
        "vehicle__name",
        "vehicle__plate_number",
    ]
    ordering_fields = ["due_date", "due_mileage", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Reminder.objects.filter(vehicle__owner=self.request.user).select_related(
            "vehicle"
        )
