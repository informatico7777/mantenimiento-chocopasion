"""URLs raíz del proyecto."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="core:dashboard", permanent=False)),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.mantenimiento.urls")),
    path("", include("apps.inventario.urls")),
    path("", include("apps.produccion.urls")),
    path("", include("apps.documentos.urls")),
    path("", include("apps.reportes.urls")),
]

# Servir archivos de media en desarrollo.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
