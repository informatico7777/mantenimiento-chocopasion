from django.urls import path

from . import views

app_name = "documentos"

urlpatterns = [
    path("documentos/", views.documento_list, name="documento_list"),
    path("documentos/subir/", views.documento_subir, name="documento_subir"),
    path("documentos/descargar/<int:pk>/", views.documento_descargar, name="documento_descargar"),
]
