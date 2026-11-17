from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle", "category", "date"]
    search_fields = [
        "description",
        "vehicle__name",
        "vehicle__plate_number",
    ]
    ordering_fields = ["date", "amount", "created_at"]
    ordering = ["-date", "-id"]

    def get_queryset(self):
        return Expense.objects.filter(vehicle__owner=self.request.user).select_related(
            "vehicle"
        )
