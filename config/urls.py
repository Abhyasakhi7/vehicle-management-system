"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.vehicles.urls")),
    path("api/v1/", include("apps.maintenance.urls")),
    path("api/v1/", include("apps.fuel.urls")),
    path("api/v1/", include("apps.expenses.urls")),
    path("api/v1/", include("apps.reminders.urls")),
    path("api/v1/", include("apps.dashboard.urls")),
    path("", RedirectView.as_view(pattern_name="dashboard"), name="home"),
    path(
        "login/",
        TemplateView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "register/",
        TemplateView.as_view(template_name="accounts/register.html"),
        name="register",
    ),
    path(
        "dashboard/",
        TemplateView.as_view(template_name="dashboard/index.html"),
        name="dashboard",
    ),
    path(
        "vehicles/",
        TemplateView.as_view(template_name="vehicles/index.html"),
        name="vehicles",
    ),
    path(
        "vehicles/<int:pk>/",
        TemplateView.as_view(template_name="vehicles/detail.html"),
        name="vehicle-detail",
    ),
    path(
        "maintenance/",
        TemplateView.as_view(template_name="maintenance/index.html"),
        name="maintenance",
    ),
    path(
        "fuel/",
        TemplateView.as_view(template_name="fuel/index.html"),
        name="fuel",
    ),
    path(
        "expenses/",
        TemplateView.as_view(template_name="expenses/index.html"),
        name="expenses",
    ),
    path(
        "reminders/",
        TemplateView.as_view(template_name="reminders/index.html"),
        name="reminders",
    ),
    path(
        "settings/",
        TemplateView.as_view(template_name="settings/index.html"),
        name="settings",
    ),
]
