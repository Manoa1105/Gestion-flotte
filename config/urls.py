"""URL principal du projet."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("comptes/", include("apps.comptes.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.flotte.urls")),
    path("missions/", include("apps.missions.urls")),
    path("finances/", include("apps.finances.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
