from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    # Áreas
    path("areas/", views.area_list, name="area_list"),
    path("areas/crear/", views.area_crear, name="area_crear"),
    path("areas/<int:pk>/editar/", views.area_editar, name="area_editar"),
    path("areas/<int:pk>/estado/", views.area_toggle, name="area_toggle"),
    # Máquinas
    path("maquinas/", views.maquina_list, name="maquina_list"),
    path("maquinas/crear/", views.maquina_crear, name="maquina_crear"),
    path("maquinas/<int:pk>/", views.maquina_detalle, name="maquina_detalle"),
    path("maquinas/<int:pk>/editar/", views.maquina_editar, name="maquina_editar"),
    # Auditoría del sistema (solo ADMINISTRADOR)
    path("auditoria/", views.auditoria_list, name="auditoria_list"),
    path("auditoria/exportar/excel/", views.auditoria_exportar_excel,
         name="auditoria_exportar_excel"),
    path("auditoria/exportar/pdf/", views.auditoria_exportar_pdf,
         name="auditoria_exportar_pdf"),
    path("auditoria/<int:pk>/", views.auditoria_detalle, name="auditoria_detalle"),
    # Componentes de máquina
    path("componentes/", views.componente_list, name="componente_list"),
    path("componentes/crear/", views.componente_crear, name="componente_crear"),
    path("componentes/<int:pk>/", views.componente_detalle, name="componente_detalle"),
    path("componentes/<int:pk>/editar/", views.componente_editar, name="componente_editar"),
    path("componentes/<int:pk>/estado/", views.componente_cambiar_estado,
         name="componente_cambiar_estado"),
    path("componentes/<int:pk>/eliminar/", views.componente_eliminar,
         name="componente_eliminar"),
    path("maquinas/<int:id_maquina>/componentes/crear/", views.componente_crear,
         name="componente_crear_maquina"),
    # Fallas probables
    path("fallas-probables/", views.falla_probable_list, name="falla_probable_list"),
    path("fallas-probables/crear/", views.falla_probable_crear, name="falla_probable_crear"),
    path("fallas-probables/<int:pk>/", views.falla_probable_detalle,
         name="falla_probable_detalle"),
    path("fallas-probables/<int:pk>/editar/", views.falla_probable_editar,
         name="falla_probable_editar"),
    path("fallas-probables/<int:pk>/eliminar/", views.falla_probable_eliminar,
         name="falla_probable_eliminar"),
    path("maquinas/<int:id_maquina>/fallas-probables/crear/", views.falla_probable_crear,
         name="falla_probable_crear_maquina"),
    # Repuestos críticos por máquina (tabla maquina_repuesto)
    path("maquinas/<int:id_maquina>/repuestos-criticos/", views.repuestos_criticos_list,
         name="repuestos_criticos_list"),
    path("maquinas/<int:id_maquina>/repuestos-criticos/agregar/",
         views.repuesto_critico_agregar, name="repuesto_critico_agregar"),
    path("maquinas/<int:id_maquina>/repuestos-criticos/<int:pk>/editar/",
         views.repuesto_critico_editar, name="repuesto_critico_editar"),
    path("maquinas/<int:id_maquina>/repuestos-criticos/<int:pk>/eliminar/",
         views.repuesto_critico_eliminar, name="repuesto_critico_eliminar"),
]
