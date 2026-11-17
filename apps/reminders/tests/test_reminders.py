from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.reminders.models import Reminder
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


def reminder_payload(**overrides):
    payload = {
        "title": "Ganti oli",
        "description": "Servis berkala",
        "due_date": "2026-12-01",
        "due_mileage": 30000,
        "status": "PENDING",
    }
    payload.update(overrides)
    return payload


class ReminderAPITests(APITestCase):
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
        self.list_url = reverse("reminders:reminder-list")
        self.vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other, **vehicle_payload(plate_number="B2222BBB")
        )

    def create_reminder(self, vehicle, **overrides):
        payload = reminder_payload(**overrides)
        if isinstance(payload["due_date"], str):
            payload["due_date"] = date.fromisoformat(payload["due_date"])
        return Reminder.objects.create(vehicle=vehicle, **payload)

    def test_create_reminder(self):
        response = self.client.post(
            self.list_url,
            reminder_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["vehicle"], self.vehicle.id)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(Reminder.objects.count(), 1)

    def test_create_with_other_vehicle_rejected(self):
        response = self.client.post(
            self.list_url,
            reminder_payload(vehicle=self.other_vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        self.assertEqual(Reminder.objects.count(), 0)

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.list_url,
            reminder_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_requires_due_date_or_due_mileage(self):
        response = self.client.post(
            self.list_url,
            reminder_payload(
                vehicle=self.vehicle.id,
                due_date=None,
                due_mileage=None,
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_only_own_reminders(self):
        self.create_reminder(self.vehicle, title="Own reminder")
        self.create_reminder(self.other_vehicle, title="Other reminder")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Own reminder")

    def test_retrieve_own_reminder(self):
        reminder = self.create_reminder(self.vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], reminder.id)

    def test_retrieve_other_reminder_returns_404(self):
        reminder = self.create_reminder(self.other_vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_reminder(self):
        reminder = self.create_reminder(self.vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.patch(url, {"status": "COMPLETED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reminder.refresh_from_db()
        self.assertEqual(reminder.status, "COMPLETED")

    def test_update_other_reminder_returns_404(self):
        reminder = self.create_reminder(self.other_vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.patch(url, {"status": "COMPLETED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_reassign_to_other_vehicle(self):
        reminder = self.create_reminder(self.vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.patch(
            url, {"vehicle": self.other_vehicle.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        reminder.refresh_from_db()
        self.assertEqual(reminder.vehicle_id, self.vehicle.id)

    def test_delete_own_reminder(self):
        reminder = self.create_reminder(self.vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reminder.objects.filter(id=reminder.id).exists())

    def test_delete_other_reminder_returns_404(self):
        reminder = self.create_reminder(self.other_vehicle)
        url = reverse("reminders:reminder-detail", args=[reminder.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Reminder.objects.filter(id=reminder.id).exists())

    def test_filter_by_status(self):
        self.create_reminder(self.vehicle, status="PENDING")
        self.create_reminder(self.vehicle, status="COMPLETED")
        response = self.client.get(self.list_url, {"status": "COMPLETED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], "COMPLETED")

    def test_search_by_title(self):
        self.create_reminder(self.vehicle, title="Ganti oli")
        self.create_reminder(self.vehicle, title="Servis rem")
        response = self.client.get(self.list_url, {"search": "rem"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Servis rem")

    def test_ordering_by_due_date(self):
        self.create_reminder(self.vehicle, due_date="2026-12-02")
        self.create_reminder(self.vehicle, due_date="2026-12-01")
        response = self.client.get(self.list_url, {"ordering": "due_date"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        due_dates = [item["due_date"] for item in response.data["results"]]
        self.assertEqual(due_dates, ["2026-12-01", "2026-12-02"])
