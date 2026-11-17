from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FuelLogViewSet

app_name = "fuel"

router = DefaultRouter()
router.register("fuel", FuelLogViewSet, basename="fuel")

urlpatterns = [
    path("", include(router.urls)),
]
