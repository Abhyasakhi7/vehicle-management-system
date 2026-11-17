from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.fuel.models import FuelLog
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


class FuelLogAPITests(APITestCase):
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
        self.list_url = reverse("fuel:fuel-list")
        self.vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other, **vehicle_payload(plate_number="B2222BBB")
        )

    def create_log(self, vehicle, **overrides):
        payload = fuel_payload(**overrides)
        if isinstance(payload["date"], str):
            payload["date"] = date.fromisoformat(payload["date"])
        payload["total_cost"] = (
            Decimal(payload["liters"]) * Decimal(payload["price_per_liter"])
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return FuelLog.objects.create(vehicle=vehicle, **payload)

    def test_create_log_and_compute_total_cost(self):
        response = self.client.post(
            self.list_url,
            fuel_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["vehicle"], self.vehicle.id)
        self.assertEqual(response.data["total_cost"], "400000.00")
        self.assertEqual(FuelLog.objects.count(), 1)

    def test_client_supplied_total_cost_is_ignored(self):
        response = self.client.post(
            self.list_url,
            fuel_payload(vehicle=self.vehicle.id, total_cost="999999.99"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_cost"], "400000.00")

    def test_create_with_other_vehicle_rejected(self):
        response = self.client.post(
            self.list_url,
            fuel_payload(vehicle=self.other_vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        self.assertEqual(FuelLog.objects.count(), 0)

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.list_url,
            fuel_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_own_logs(self):
        self.create_log(self.vehicle, station_name="Own station")
        self.create_log(self.other_vehicle, station_name="Other station")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["station_name"], "Own station")

    def test_retrieve_own_log(self):
        log = self.create_log(self.vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], log.id)

    def test_retrieve_other_log_returns_404(self):
        log = self.create_log(self.other_vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_log_recomputes_total_cost(self):
        log = self.create_log(self.vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.patch(url, {"liters": "50.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_cost"], "500000.00")
        log.refresh_from_db()
        self.assertEqual(str(log.total_cost), "500000.00")

    def test_update_other_log_returns_404(self):
        log = self.create_log(self.other_vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.patch(url, {"liters": "50.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_reassign_to_other_vehicle(self):
        log = self.create_log(self.vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.patch(
            url, {"vehicle": self.other_vehicle.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        log.refresh_from_db()
        self.assertEqual(log.vehicle_id, self.vehicle.id)

    def test_delete_own_log(self):
        log = self.create_log(self.vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FuelLog.objects.filter(id=log.id).exists())

    def test_delete_other_log_returns_404(self):
        log = self.create_log(self.other_vehicle)
        url = reverse("fuel:fuel-detail", args=[log.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(FuelLog.objects.filter(id=log.id).exists())

    def test_invalid_liters_rejected(self):
        response = self.client.post(
            self.list_url,
            fuel_payload(vehicle=self.vehicle.id, liters="0.00"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("liters", response.data)

    def test_negative_price_rejected(self):
        response = self.client.post(
            self.list_url,
            fuel_payload(vehicle=self.vehicle.id, price_per_liter="-1.00"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price_per_liter", response.data)

    def test_filter_by_is_full_tank(self):
        self.create_log(self.vehicle, is_full_tank=True)
        self.create_log(self.vehicle, is_full_tank=False)
        response = self.client.get(self.list_url, {"is_full_tank": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(response.data["results"][0]["is_full_tank"])

    def test_search_by_station_name(self):
        self.create_log(self.vehicle, station_name="Shell")
        self.create_log(self.vehicle, station_name="Pertamina")
        response = self.client.get(self.list_url, {"search": "Pertamina"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["station_name"], "Pertamina")

    def test_ordering_by_total_cost(self):
        self.create_log(self.vehicle, liters="10.00")
        self.create_log(self.vehicle, liters="30.00")
        response = self.client.get(self.list_url, {"ordering": "total_cost"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        totals = [item["total_cost"] for item in response.data["results"]]
        self.assertEqual(totals, ["100000.00", "300000.00"])
