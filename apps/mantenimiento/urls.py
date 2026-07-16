from django.urls import path

from . import views

app_name = "mantenimiento"

urlpatterns = [
    # Checklist
    path("checklist/plantillas/", views.checklist_plantillas, name="checklist_plantillas"),
    path("checklist/plantillas/crear/", views.checklist_plantilla_crear,
         name="checklist_plantilla_crear"),
    path("checklist/", views.checklist_list, name="checklist_list"),
    path("checklist/ejecutar/<int:id_maquina>/", views.checklist_ejecutar,
         name="checklist_ejecutar"),
    path("checklist/<int:pk>/", views.checklist_detalle, name="checklist_detalle"),
    path("checklist/<int:pk>/generar-falla/", views.checklist_generar_falla,
         name="checklist_generar_falla"),
    # Observaciones
    path("observaciones/", views.observacion_list, name="observacion_list"),
    path("observaciones/crear/", views.observacion_crear, name="observacion_crear"),
    path("observaciones/<int:pk>/convertir-falla/", views.observacion_convertir_falla,
         name="observacion_convertir_falla"),
    # Fallas
    path("fallas/", views.falla_list, name="falla_list"),
    path("fallas/crear/", views.falla_crear, name="falla_crear"),
    path("fallas/<int:pk>/", views.falla_detalle, name="falla_detalle"),
    path("fallas/<int:pk>/convertir-ot/", views.falla_convertir_ot, name="falla_convertir_ot"),
    # Órdenes de trabajo
    path("ordenes/", views.ot_list, name="ot_list"),
    path("ordenes/crear/", views.ot_crear, name="ot_crear"),
    path("ordenes/<int:pk>/", views.ot_detalle, name="ot_detalle"),
    path("ordenes/<int:pk>/editar/", views.ot_editar, name="ot_editar"),
]
