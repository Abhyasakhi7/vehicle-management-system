from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:register")
        self.payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertEqual(response.data["user"]["email"], "newuser@example.com")

    def test_register_password_mismatch(self):
        self.payload["password_confirm"] = "Different123"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username="newuser",
            email="other@example.com",
            password="StrongPass123",
        )
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            username="other",
            email="newuser@example.com",
            password="StrongPass123",
        )
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_weak_password(self):
        self.payload["password"] = "12345678"
        self.payload["password_confirm"] = "12345678"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_ignores_privileged_fields(self):
        self.payload["is_staff"] = True
        self.payload["is_superuser"] = True
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_register_normalizes_email(self):
        self.payload["email"] = "NewUser@Example.COM"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], "newuser@example.com")


class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123",
        )

    def test_login_with_username(self):
        response = self.client.post(
            self.url,
            {"identifier": "loginuser", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_with_email(self):
        response = self.client.post(
            self.url,
            {"identifier": "login@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.url,
            {"identifier": "loginuser", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid credentials.")

    def test_login_unknown_identifier(self):
        response = self.client.post(
            self.url,
            {"identifier": "nobody", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CurrentUserTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:me")
        self.user = User.objects.create_user(
            username="meuser",
            email="me@example.com",
            password="StrongPass123",
        )
        self.token = Token.objects.create(user=self.user)

    def test_me_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "meuser")


class LogoutTests(APITestCase):
    def setUp(self):
        self.url = reverse("accounts:logout")
        self.user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="StrongPass123",
        )
        self.token = Token.objects.create(user=self.user)

    def test_logout_requires_auth(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_deletes_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())
