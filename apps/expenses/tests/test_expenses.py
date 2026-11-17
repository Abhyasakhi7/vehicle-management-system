from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.expenses.models import Expense
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


def expense_payload(**overrides):
    payload = {
        "category": "TAX",
        "description": "Pajak tahunan",
        "amount": "500000.00",
        "date": "2026-02-01",
    }
    payload.update(overrides)
    return payload


class ExpenseAPITests(APITestCase):
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
        self.list_url = reverse("expenses:expense-list")
        self.vehicle = Vehicle.objects.create(owner=self.user, **vehicle_payload())
        self.other_vehicle = Vehicle.objects.create(
            owner=self.other, **vehicle_payload(plate_number="B2222BBB")
        )

    def create_expense(self, vehicle, **overrides):
        payload = expense_payload(**overrides)
        if isinstance(payload["date"], str):
            payload["date"] = date.fromisoformat(payload["date"])
        return Expense.objects.create(vehicle=vehicle, **payload)

    def test_create_expense(self):
        response = self.client.post(
            self.list_url,
            expense_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["vehicle"], self.vehicle.id)
        self.assertEqual(response.data["amount"], "500000.00")
        self.assertEqual(Expense.objects.count(), 1)

    def test_create_with_other_vehicle_rejected(self):
        response = self.client.post(
            self.list_url,
            expense_payload(vehicle=self.other_vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        self.assertEqual(Expense.objects.count(), 0)

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.list_url,
            expense_payload(vehicle=self.vehicle.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_own_expenses(self):
        self.create_expense(self.vehicle, description="Own expense")
        self.create_expense(self.other_vehicle, description="Other expense")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["description"], "Own expense")

    def test_retrieve_own_expense(self):
        expense = self.create_expense(self.vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], expense.id)

    def test_retrieve_other_expense_returns_404(self):
        expense = self.create_expense(self.other_vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_expense(self):
        expense = self.create_expense(self.vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.patch(
            url, {"amount": "750000.00"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(str(expense.amount), "750000.00")

    def test_update_other_expense_returns_404(self):
        expense = self.create_expense(self.other_vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.patch(
            url, {"amount": "750000.00"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_reassign_to_other_vehicle(self):
        expense = self.create_expense(self.vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.patch(
            url, {"vehicle": self.other_vehicle.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vehicle", response.data)
        expense.refresh_from_db()
        self.assertEqual(expense.vehicle_id, self.vehicle.id)

    def test_delete_own_expense(self):
        expense = self.create_expense(self.vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())

    def test_delete_other_expense_returns_404(self):
        expense = self.create_expense(self.other_vehicle)
        url = reverse("expenses:expense-detail", args=[expense.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Expense.objects.filter(id=expense.id).exists())

    def test_invalid_category_rejected(self):
        response = self.client.post(
            self.list_url,
            expense_payload(vehicle=self.vehicle.id, category="FOOD"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)

    def test_negative_amount_rejected(self):
        response = self.client.post(
            self.list_url,
            expense_payload(vehicle=self.vehicle.id, amount="-1.00"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_filter_by_category(self):
        self.create_expense(self.vehicle, category="TAX")
        self.create_expense(self.vehicle, category="INSURANCE")
        response = self.client.get(self.list_url, {"category": "INSURANCE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["category"], "INSURANCE")

    def test_search_by_description(self):
        self.create_expense(self.vehicle, description="Pajak tahunan")
        self.create_expense(self.vehicle, description="Asuransi")
        response = self.client.get(self.list_url, {"search": "Asuransi"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["description"], "Asuransi")

    def test_ordering_by_amount(self):
        self.create_expense(self.vehicle, amount="700000.00")
        self.create_expense(self.vehicle, amount="300000.00")
        response = self.client.get(self.list_url, {"ordering": "amount"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        amounts = [item["amount"] for item in response.data["results"]]
        self.assertEqual(amounts, ["300000.00", "700000.00"])
