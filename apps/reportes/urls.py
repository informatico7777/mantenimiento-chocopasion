from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("reportes/", views.reporte_list, name="reporte_list"),
    path("reportes/semanal/", views.reporte_semanal, name="reporte_semanal"),
    path("reportes/descargar/<int:pk>/", views.reporte_descargar, name="reporte_descargar"),
    # --- Indicadores de mantenimiento ---
    path("indicadores/", views.indicadores_view, name="indicadores"),
    path("indicadores/calcular/", views.indicador_calcular, name="indicador_calcular"),
    path("indicadores/maquina/<int:pk>/", views.indicador_maquina_detalle,
         name="indicador_maquina_detalle"),
    path("indicadores/exportar/pdf/", views.indicador_exportar_pdf,
         name="indicador_exportar_pdf"),
    path("indicadores/exportar/excel/", views.indicador_exportar_excel,
         name="indicador_exportar_excel"),
]
