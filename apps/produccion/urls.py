from django.urls import path

from . import views

app_name = "produccion"

urlpatterns = [
    path("produccion/lotes/", views.lote_list, name="lote_list"),
    path("produccion/lotes/crear/", views.lote_crear, name="lote_crear"),
    path("energia/", views.consumo_list, name="consumo_list"),
    path("energia/crear/", views.consumo_crear, name="consumo_crear"),
]
