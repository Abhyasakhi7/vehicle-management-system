from datetime import date
from decimal import Decimal

from django.db.models import Max, Min, Sum
from django.db.models.functions import TruncMonth
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.expenses.models import Expense
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceRecord
from apps.vehicles.models import Vehicle

MONTHS_IN_GRAPH = 6
RECENT_ACTIVITY_LIMIT = 10
RECENT_ACTIVITY_QUERY_LIMIT = 50
UPCOMING_MAINTENANCE_LIMIT = 10


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date, end_date, error = self._parse_period(request)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        vehicle_ids = list(
            Vehicle.objects.filter(owner=user).values_list("id", flat=True)
        )

        maintenance_qs = MaintenanceRecord.objects.filter(vehicle_id__in=vehicle_ids)
        fuel_qs = FuelLog.objects.filter(vehicle_id__in=vehicle_ids)
        expense_qs = Expense.objects.filter(vehicle_id__in=vehicle_ids)

        if start_date:
            maintenance_qs = maintenance_qs.filter(service_date__gte=start_date)
            fuel_qs = fuel_qs.filter(date__gte=start_date)
            expense_qs = expense_qs.filter(date__gte=start_date)
        if end_date:
            maintenance_qs = maintenance_qs.filter(service_date__lte=end_date)
            fuel_qs = fuel_qs.filter(date__lte=end_date)
            expense_qs = expense_qs.filter(date__lte=end_date)

        maintenance_total = self._sum(maintenance_qs, "cost")
        fuel_total = self._sum(fuel_qs, "total_cost")
        expense_total = self._sum(expense_qs, "amount")
        total_cost = maintenance_total + fuel_total + expense_total

        return Response(
            {
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                },
                "total_vehicles": len(vehicle_ids),
                "total_cost": self._money(total_cost),
                "cost_breakdown": {
                    "maintenance": self._money(maintenance_total),
                    "fuel": self._money(fuel_total),
                    "expenses": self._money(expense_total),
                },
                "total_distance": self._total_distance(fuel_qs),
                "recent_activity": self._recent_activity(
                    maintenance_qs, fuel_qs, expense_qs
                ),
                "upcoming_maintenance": self._upcoming_maintenance(user),
                "monthly_expenses": self._monthly_expenses(user),
            }
        )

    def _parse_period(self, request):
        start_date_raw = request.query_params.get("start_date")
        end_date_raw = request.query_params.get("end_date")
        start_date = self._parse_date(start_date_raw)
        end_date = self._parse_date(end_date_raw)

        if start_date_raw and start_date is None:
            return None, None, "Invalid start_date. Use YYYY-MM-DD."
        if end_date_raw and end_date is None:
            return None, None, "Invalid end_date. Use YYYY-MM-DD."
        if start_date and end_date and start_date > end_date:
            return None, None, "start_date cannot be after end_date."
        return start_date, end_date, None

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _sum(queryset, field):
        total = queryset.aggregate(total=Sum(field)).get("total") or Decimal("0")
        return total.quantize(Decimal("0.01"))

    @staticmethod
    def _money(value):
        return str(value.quantize(Decimal("0.01")))

    @staticmethod
    def _total_distance(fuel_qs):
        vehicle_mileage = (
            fuel_qs.order_by()
            .values("vehicle_id")
            .annotate(min_mileage=Min("mileage"), max_mileage=Max("mileage"))
        )
        distance = 0
        for item in vehicle_mileage:
            if item["min_mileage"] is not None:
                distance += item["max_mileage"] - item["min_mileage"]
        return distance

    def _recent_activity(self, maintenance_qs, fuel_qs, expense_qs):
        items = []

        maintenance_records = (
            maintenance_qs.select_related("vehicle")
            .order_by("-created_at")[:RECENT_ACTIVITY_QUERY_LIMIT]
        )
        for record in maintenance_records:
            items.append(
                {
                    "type": "maintenance",
                    "id": record.id,
                    "vehicle": self._vehicle_summary(record.vehicle),
                    "date": record.service_date.isoformat(),
                    "created_at": record.created_at.isoformat(),
                    "amount": self._money(record.cost),
                    "description": record.description
                    or record.get_service_type_display(),
                }
            )

        fuel_records = (
            fuel_qs.select_related("vehicle").order_by("-created_at")[
                :RECENT_ACTIVITY_QUERY_LIMIT
            ]
        )
        for record in fuel_records:
            description = f"{record.liters} L @ {record.price_per_liter}"
            if record.station_name:
                description = f"{description} - {record.station_name}"
            items.append(
                {
                    "type": "fuel",
                    "id": record.id,
                    "vehicle": self._vehicle_summary(record.vehicle),
                    "date": record.date.isoformat(),
                    "created_at": record.created_at.isoformat(),
                    "amount": self._money(record.total_cost),
                    "description": description,
                }
            )

        expense_records = (
            expense_qs.select_related("vehicle")
            .order_by("-created_at")[:RECENT_ACTIVITY_QUERY_LIMIT]
        )
        for record in expense_records:
            items.append(
                {
                    "type": "expense",
                    "id": record.id,
                    "vehicle": self._vehicle_summary(record.vehicle),
                    "date": record.date.isoformat(),
                    "created_at": record.created_at.isoformat(),
                    "amount": self._money(record.amount),
                    "description": record.description,
                }
            )

        items.sort(key=lambda item: item["created_at"], reverse=True)
        return items[:RECENT_ACTIVITY_LIMIT]

    @staticmethod
    def _vehicle_summary(vehicle):
        return {
            "id": vehicle.id,
            "name": vehicle.name,
            "plate_number": vehicle.plate_number,
        }

    def _upcoming_maintenance(self, user):
        today = date.today()
        records = (
            MaintenanceRecord.objects.filter(
                vehicle__owner=user,
                next_service_date__gte=today,
            )
            .select_related("vehicle")
            .order_by("next_service_date")[:UPCOMING_MAINTENANCE_LIMIT]
        )
        return [
            {
                "id": record.id,
                "vehicle": self._vehicle_summary(record.vehicle),
                "service_type": record.service_type,
                "service_date": record.service_date.isoformat(),
                "next_service_date": (
                    record.next_service_date.isoformat()
                    if record.next_service_date
                    else None
                ),
                "next_service_mileage": record.next_service_mileage,
                "mileage": record.mileage,
                "cost": self._money(record.cost),
            }
            for record in records
        ]

    def _monthly_expenses(self, user):
        maintenance_months = (
            MaintenanceRecord.objects.filter(vehicle__owner=user)
            .annotate(month=TruncMonth("service_date"))
            .values("month")
            .annotate(total=Sum("cost"))
        )
        fuel_months = (
            FuelLog.objects.filter(vehicle__owner=user)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("total_cost"))
        )
        expense_months = (
            Expense.objects.filter(vehicle__owner=user)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
        )

        maintenance_by_month = {
            item["month"].strftime("%Y-%m"): item["total"] or Decimal("0")
            for item in maintenance_months
        }
        fuel_by_month = {
            item["month"].strftime("%Y-%m"): item["total"] or Decimal("0")
            for item in fuel_months
        }
        expense_by_month = {
            item["month"].strftime("%Y-%m"): item["total"] or Decimal("0")
            for item in expense_months
        }

        result = []
        for month in self._last_months():
            maintenance_total = maintenance_by_month.get(month, Decimal("0"))
            fuel_total = fuel_by_month.get(month, Decimal("0"))
            expense_total = expense_by_month.get(month, Decimal("0"))
            result.append(
                {
                    "month": month,
                    "maintenance": self._money(maintenance_total),
                    "fuel": self._money(fuel_total),
                    "expenses": self._money(expense_total),
                    "total": self._money(
                        maintenance_total + fuel_total + expense_total
                    ),
                }
            )
        return result

    @staticmethod
    def _last_months():
        today = date.today()
        months = []
        for offset in range(MONTHS_IN_GRAPH - 1, -1, -1):
            month_index = today.year * 12 + today.month - 1 - offset
            year = month_index // 12
            month = month_index % 12 + 1
            months.append(date(year, month, 1).strftime("%Y-%m"))
        return months
