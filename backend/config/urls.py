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

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from challenges.adapters.views import calendar_view


def health_check(request):
    """GET /api/health/: return the backend health status."""
    return JsonResponse({"status": "ok"})


def index(request):
    """GET /: return the backend service status."""
    return JsonResponse({"service": "bam-boo backend", "status": "ok"})


urlpatterns = [
    path("", index, name="index"),
    path("api/health/", health_check, name="health-check"),
    path("api/challenges/", include("challenges.urls")),
    path("api/attempts/", include("play.urls")),
    path("api/users/", include("users.urls")),
    path("admin/", admin.site.urls),
    path("api/calendar/", calendar_view, name="calendar"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
