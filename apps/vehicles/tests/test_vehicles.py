from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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


class VehicleAPITests(APITestCase):
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
        self.list_url = reverse("vehicles:vehicle-list")

    def create_vehicle(self, owner, **overrides):
        return Vehicle.objects.create(owner=owner, **vehicle_payload(**overrides))

    def test_create_vehicle(self):
        response = self.client.post(self.list_url, vehicle_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.user.id)
        self.assertEqual(Vehicle.objects.count(), 1)

    def test_owner_cannot_be_set_from_client(self):
        response = self.client.post(
            self.list_url,
            vehicle_payload(owner=self.other.id),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.user.id)

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.list_url, vehicle_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_own_vehicles(self):
        self.create_vehicle(self.user, plate_number="B1111AAA")
        self.create_vehicle(self.other, plate_number="B2222BBB")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["plate_number"], "B1111AAA")

    def test_retrieve_own_vehicle(self):
        vehicle = self.create_vehicle(self.user)
        url = reverse("vehicles:vehicle-detail", args=[vehicle.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["plate_number"], vehicle.plate_number)

    def test_retrieve_other_vehicle_returns_404(self):
        vehicle = self.create_vehicle(self.other)
        url = reverse("vehicles:vehicle-detail", args=[vehicle.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_vehicle(self):
        vehicle = self.create_vehicle(self.user)
        url = reverse("vehicles:vehicle-detail", args=[vehicle.id])
        response = self.client.patch(url, {"mileage": 20000}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.mileage, 20000)

    def test_update_other_vehicle_returns_404(self):
        vehicle = self.create_vehicle(self.other)
        url = reverse("vehicles:vehicle-detail", args=[vehicle.id])
        response = self.client.patch(url, {"mileage": 20000}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_vehicle(self):
        vehicle = self.create_vehicle(self.user)
        url = reverse("vehicles:vehicle-detail", args=[vehicle.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.filter(id=vehicle.id).exists())

    def test_delete_other_vehicle_returns_404(self):
        vehicle = self.create_vehicle(self.other)
        url = reverse("vehicles:vehicle-detail", args=[vehicle.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Vehicle.objects.filter(id=vehicle.id).exists())

    def test_duplicate_plate_rejected(self):
        self.create_vehicle(self.user, plate_number="B9999ZZZ")
        response = self.client.post(
            self.list_url,
            vehicle_payload(plate_number="B9999ZZZ"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plate_number", response.data)

    def test_plate_number_is_globally_unique(self):
        self.create_vehicle(self.other, plate_number="B8888YYY")
        response = self.client.post(
            self.list_url,
            vehicle_payload(plate_number="B8888YYY"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_year_rejected(self):
        response = self.client.post(
            self.list_url,
            vehicle_payload(year=1800),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("year", response.data)

    def test_negative_mileage_rejected(self):
        response = self.client.post(
            self.list_url,
            vehicle_payload(mileage=-1),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mileage", response.data)

    def test_invalid_fuel_type_rejected(self):
        response = self.client.post(
            self.list_url,
            vehicle_payload(fuel_type="WATER"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fuel_type", response.data)

    def test_filter_by_vehicle_type(self):
        self.create_vehicle(self.user, plate_number="B1111AAA", vehicle_type="CAR")
        self.create_vehicle(
            self.user,
            plate_number="B2222BBB",
            vehicle_type="MOTORCYCLE",
        )
        response = self.client.get(self.list_url, {"vehicle_type": "MOTORCYCLE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["plate_number"], "B2222BBB")

    def test_search_by_name(self):
        self.create_vehicle(self.user, plate_number="B1111AAA", name="Daily Car")
        self.create_vehicle(self.user, plate_number="B2222BBB", name="Weekend Bike")
        response = self.client.get(self.list_url, {"search": "Weekend"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Weekend Bike")

    def test_ordering_by_mileage(self):
        self.create_vehicle(self.user, plate_number="B1111AAA", mileage=5000)
        self.create_vehicle(self.user, plate_number="B2222BBB", mileage=9000)
        response = self.client.get(self.list_url, {"ordering": "mileage"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mileages = [item["mileage"] for item in response.data["results"]]
        self.assertEqual(mileages, [5000, 9000])

    def test_pagination(self):
        for index in range(25):
            self.create_vehicle(self.user, plate_number=f"B{index:04d}AAA")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
