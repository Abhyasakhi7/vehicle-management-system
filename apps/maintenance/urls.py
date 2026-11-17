from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceRecordViewSet

app_name = "maintenance"

router = DefaultRouter()
router.register("maintenance", MaintenanceRecordViewSet, basename="maintenance")

urlpatterns = [
    path("", include(router.urls)),
]
