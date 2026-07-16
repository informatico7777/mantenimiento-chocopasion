from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("repuestos/", views.repuesto_list, name="repuesto_list"),
    path("repuestos/crear/", views.repuesto_crear, name="repuesto_crear"),
    path("repuestos/<int:pk>/editar/", views.repuesto_editar, name="repuesto_editar"),
    path("repuestos/<int:pk>/movimiento/", views.repuesto_movimiento, name="repuesto_movimiento"),
    path("proveedores/", views.proveedor_list, name="proveedor_list"),
    path("proveedores/crear/", views.proveedor_crear, name="proveedor_crear"),
    path("proveedores/<int:pk>/editar/", views.proveedor_editar, name="proveedor_editar"),
    path("servicios-externos/", views.servicio_list, name="servicio_list"),
    path("servicios-externos/crear/", views.servicio_crear, name="servicio_crear"),
]
