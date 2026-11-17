from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class MaintenanceRecordAPITests(APITestCase):
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
        self.list_url = reverse("maintenance:maintenance-list")
        self.vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other, **vehicle_payload(plate_number="B2222BBB")
        )

    def create_record(self, vehicle, **overrides):
        payload = maintenance_payload(**overrides)
        payload["service_date"] = date.fromisoformat(payload["service_date"])
        if isinstance(payload.get("next_service_date"), str):
            payload["next_service_date"] = date.fromisoformat(
                payload["next_service_date"]
            )
        return MaintenanceRecord.objects.create(vehicle=vehicle, **payload)

    def test_create_record(self):
        response = self.client.post(
            self.list_url,
            maintenance_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["vehicle"], self.vehicle.id)
        self.assertEqual(response.data["cost"], "250000.00")
        self.assertEqual(response.data["next_service_date"], "2026-04-15")
        self.assertEqual(MaintenanceRecord.objects.count(), 1)

    def test_create_with_other_vehicle_rejected(self):
        response = self.client.post(
            self.list_url,
            maintenance_payload(vehicle=self.other_vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        self.assertEqual(MaintenanceRecord.objects.count(), 0)

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.list_url,
            maintenance_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_own_records(self):
        self.create_record(self.vehicle, description="Own record")
        self.create_record(self.other_vehicle, description="Other record")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["description"], "Own record")

    def test_retrieve_own_record(self):
        record = self.create_record(self.vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], record.id)

    def test_retrieve_other_record_returns_404(self):
        record = self.create_record(self.other_vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_record(self):
        record = self.create_record(self.vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.patch(url, {"cost": "300000.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record.refresh_from_db()
        self.assertEqual(str(record.cost), "300000.00")

    def test_update_other_record_returns_404(self):
        record = self.create_record(self.other_vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.patch(url, {"cost": "300000.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_reassign_to_other_vehicle(self):
        record = self.create_record(self.vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.patch(
            url, {"vehicle": self.other_vehicle.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        record.refresh_from_db()
        self.assertEqual(record.vehicle_id, self.vehicle.id)

    def test_delete_own_record(self):
        record = self.create_record(self.vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MaintenanceRecord.objects.filter(id=record.id).exists())

    def test_delete_other_record_returns_404(self):
        record = self.create_record(self.other_vehicle)
        url = reverse("maintenance:maintenance-detail", args=[record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(MaintenanceRecord.objects.filter(id=record.id).exists())

    def test_next_service_date_before_service_date_rejected(self):
        response = self.client.post(
            self.list_url,
            maintenance_payload(
                vehicle=self.vehicle.id,
                next_service_date="2025-12-31",
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("next_service_date", response.data)

    def test_next_service_mileage_less_than_current_rejected(self):
        response = self.client.post(
            self.list_url,
            maintenance_payload(
                vehicle=self.vehicle.id,
                next_service_mileage=15000,
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("next_service_mileage", response.data)

    def test_filter_by_vehicle(self):
        second_vehicle = Vehicle.objects.create(
            owner=self.user, **vehicle_payload(plate_number="B3333CCC")
        )
        self.create_record(self.vehicle, description="First")
        self.create_record(second_vehicle, description="Second")
        response = self.client.get(self.list_url, {"vehicle": self.vehicle.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["description"], "First")

    def test_search_by_description(self):
        self.create_record(self.vehicle, description="Ganti oli")
        self.create_record(self.vehicle, description="Servis rem")
        response = self.client.get(self.list_url, {"search": "rem"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["description"], "Servis rem")

    def test_ordering_by_cost(self):
        self.create_record(self.vehicle, cost="300000.00")
        self.create_record(self.vehicle, cost="100000.00")
        response = self.client.get(self.list_url, {"ordering": "cost"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        costs = [item["cost"] for item in response.data["results"]]
        self.assertEqual(costs, ["100000.00", "300000.00"])

    def test_pagination(self):
        records = []
        for _ in range(25):
            payload = maintenance_payload()
            payload["service_date"] = date.fromisoformat(payload["service_date"])
            payload["next_service_date"] = date.fromisoformat(
                payload["next_service_date"]
            )
            records.append(MaintenanceRecord(vehicle=self.vehicle, **payload))
        MaintenanceRecord.objects.bulk_create(records)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
