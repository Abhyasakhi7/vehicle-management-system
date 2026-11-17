from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.expenses.models import Expense
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceRecord
from apps.vehicles.models import Vehicle

User = get_user_model()


def vehicle_payload(**overrides):
    payload = {
        "name": "Daily Car",
        "brand": "Toyota",
        "model": "Avanza",
        "year": 2020,
        "vehicle_type": "CAR",
        "plate_number": "B1234XYZ",
        "fuel_type": "PETROL",
        "transmission": "AUTOMATIC",
        "mileage": 15000,
        "color": "Silver",
    }
    payload.update(overrides)
    return payload


def maintenance_payload(**overrides):
    payload = {
        "service_type": "OIL_CHANGE",
        "description": "Ganti oli",
        "service_date": "2026-01-15",
        "mileage": 20000,
        "cost": "250000.00",
        "workshop_name": "Bengkel A",
        "next_service_date": "2026-04-15",
        "next_service_mileage": 30000,
    }
    payload.update(overrides)
    return payload


def fuel_payload(**overrides):
    payload = {
        "date": "2026-01-10",
        "mileage": 20000,
        "liters": "40.00",
        "price_per_liter": "10000.00",
        "is_full_tank": True,
        "station_name": "Shell",
    }
    payload.update(overrides)
    return payload


def expense_payload(**overrides):
    payload = {
        "category": "TAX",
        "description": "Pajak tahunan",
        "amount": "500000.00",
        "date": "2026-02-01",
    }
    payload.update(overrides)
    return payload


def previous_month(value):
    month_index = value.year * 12 + value.month - 2
    return date(month_index // 12, month_index % 12 + 1, 1)


class DashboardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPass123",
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPass123",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("dashboard:dashboard")

    def create_maintenance(self, vehicle, **overrides):
        payload = maintenance_payload(**overrides)
        if isinstance(payload["service_date"], str):
            payload["service_date"] = date.fromisoformat(payload["service_date"])
        if isinstance(payload.get("next_service_date"), str):
            payload["next_service_date"] = date.fromisoformat(
                payload["next_service_date"]
            )
        return MaintenanceRecord.objects.create(vehicle=vehicle, **payload)

    def create_fuel(self, vehicle, **overrides):
        payload = fuel_payload(**overrides)
        if isinstance(payload["date"], str):
            payload["date"] = date.fromisoformat(payload["date"])
        payload["total_cost"] = (
            Decimal(payload["liters"]) * Decimal(payload["price_per_liter"])
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return FuelLog.objects.create(vehicle=vehicle, **payload)

    def create_expense(self, vehicle, **overrides):
        payload = expense_payload(**overrides)
        if isinstance(payload["date"], str):
            payload["date"] = date.fromisoformat(payload["date"])
        return Expense.objects.create(vehicle=vehicle, **payload)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_dashboard(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["period"], {"start_date": None, "end_date": None})
        self.assertEqual(response.data["total_vehicles"], 0)
        self.assertEqual(response.data["total_cost"], "0.00")
        self.assertEqual(response.data["cost_breakdown"]["maintenance"], "0.00")
        self.assertEqual(response.data["cost_breakdown"]["fuel"], "0.00")
        self.assertEqual(response.data["cost_breakdown"]["expenses"], "0.00")
        self.assertEqual(response.data["total_distance"], 0)
        self.assertEqual(response.data["recent_activity"], [])
        self.assertEqual(response.data["upcoming_maintenance"], [])
        self.assertEqual(len(response.data["monthly_expenses"]), 6)
        for item in response.data["monthly_expenses"]:
            self.assertEqual(item["total"], "0.00")

    def test_aggregates_and_isolates_users(self):
        vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        Vehicle.objects.create(
            owner=self.user, **vehicle_payload(plate_number="B3333CCC")
        )
        other_vehicle = Vehicle.objects.create(
            owner=self.other, **vehicle_payload(plate_number="B2222BBB")
        )
        today = date.today()

        self.create_maintenance(
            vehicle,
            service_date=today,
            next_service_date=(today + timedelta(days=5)).isoformat(),
        )
        self.create_fuel(vehicle, date=today)
        self.create_expense(vehicle, date=today)
        self.create_maintenance(
            other_vehicle,
            service_date=today,
            next_service_date=(today + timedelta(days=5)).isoformat(),
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_vehicles"], 2)
        self.assertEqual(response.data["total_cost"], "1150000.00")
        self.assertEqual(response.data["cost_breakdown"]["maintenance"], "250000.00")
        self.assertEqual(response.data["cost_breakdown"]["fuel"], "400000.00")
        self.assertEqual(response.data["cost_breakdown"]["expenses"], "500000.00")
        self.assertEqual(response.data["total_distance"], 0)

        self.assertEqual(len(response.data["recent_activity"]), 3)
        types = {item["type"] for item in response.data["recent_activity"]}
        self.assertEqual(types, {"maintenance", "fuel", "expense"})
        self.assertTrue(
            all(
                item["vehicle"]["id"] != other_vehicle.id
                for item in response.data["recent_activity"]
            )
        )
        amounts = {item["type"]: item["amount"] for item in response.data["recent_activity"]}
        self.assertEqual(amounts["maintenance"], "250000.00")
        self.assertEqual(amounts["fuel"], "400000.00")
        self.assertEqual(amounts["expense"], "500000.00")

        self.assertEqual(len(response.data["upcoming_maintenance"]), 1)
        self.assertEqual(
            response.data["upcoming_maintenance"][0]["vehicle"]["id"], vehicle.id
        )

        monthly = {
            item["month"]: item for item in response.data["monthly_expenses"]
        }
        current_month = today.strftime("%Y-%m")
        self.assertEqual(monthly[current_month]["total"], "1150000.00")

    def test_date_range_filter(self):
        vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        today = date.today()
        first_of_month = today.replace(day=1)
        prev_month = previous_month(today)

        self.create_maintenance(
            vehicle, service_date=first_of_month, next_service_date=None
        )
        self.create_fuel(vehicle, date=prev_month)
        self.create_expense(vehicle, date=first_of_month)

        response = self.client.get(
            self.url,
            {
                "start_date": first_of_month.isoformat(),
                "end_date": today.isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["period"],
            {
                "start_date": first_of_month.isoformat(),
                "end_date": today.isoformat(),
            },
        )
        self.assertEqual(response.data["total_cost"], "750000.00")
        self.assertEqual(response.data["cost_breakdown"]["maintenance"], "250000.00")
        self.assertEqual(response.data["cost_breakdown"]["fuel"], "0.00")
        self.assertEqual(response.data["cost_breakdown"]["expenses"], "500000.00")
        self.assertEqual(response.data["total_distance"], 0)
        types = {item["type"] for item in response.data["recent_activity"]}
        self.assertEqual(types, {"maintenance", "expense"})

    def test_invalid_period_rejected(self):
        response = self.client.get(self.url, {"start_date": "not-a-date"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(
            self.url,
            {"start_date": "2026-02-01", "end_date": "2026-01-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_distance_and_upcoming_maintenance(self):
        vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        today = date.today()

        self.create_fuel(vehicle, date=today, mileage=1000)
        self.create_fuel(vehicle, date=today, mileage=3000)
        self.create_maintenance(
            vehicle,
            service_date=today,
            next_service_date=(today + timedelta(days=5)).isoformat(),
        )
        self.create_maintenance(
            vehicle,
            service_date=today,
            next_service_date=(today - timedelta(days=5)).isoformat(),
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_distance"], 2000)
        self.assertEqual(len(response.data["recent_activity"]), 4)
        types = {item["type"] for item in response.data["recent_activity"]}
        self.assertEqual(types, {"maintenance", "fuel"})
        self.assertEqual(len(response.data["upcoming_maintenance"]), 1)
        self.assertEqual(
            response.data["upcoming_maintenance"][0]["next_service_date"],
            (today + timedelta(days=5)).isoformat(),
        )

    def test_monthly_expenses(self):
        vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        today = date.today()
        first_of_month = today.replace(day=1)
        prev_month = previous_month(today)

        self.create_maintenance(
            vehicle, service_date=first_of_month, next_service_date=None
        )
        self.create_expense(vehicle, date=prev_month)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        monthly = {
            item["month"]: item for item in response.data["monthly_expenses"]
        }
        current_month = first_of_month.strftime("%Y-%m")
        previous_month_key = prev_month.strftime("%Y-%m")
        self.assertEqual(monthly[current_month]["maintenance"], "250000.00")
        self.assertEqual(monthly[previous_month_key]["expenses"], "500000.00")
        self.assertEqual(monthly[previous_month_key]["total"], "500000.00")

    def test_other_user_data_is_not_included(self):
        other_vehicle = Vehicle.objects.create(
            owner=self.other, **vehicle_payload(plate_number="B2222BBB")
        )
        self.create_maintenance(other_vehicle, next_service_date=None)
        self.create_fuel(other_vehicle)
        self.create_expense(other_vehicle)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_vehicles"], 0)
        self.assertEqual(response.data["total_cost"], "0.00")
        self.assertEqual(response.data["recent_activity"], [])
        self.assertEqual(response.data["upcoming_maintenance"], [])
