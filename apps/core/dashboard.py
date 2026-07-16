"""Lógica de agregación para el dashboard principal."""
from datetime import timedelta

from django.db.models import Count, F, Q
from django.utils import timezone
from datetime import date

def construir_contexto_dashboard():
    from apps.inventario.models import Repuesto
    from apps.mantenimiento.models import (
        ObservacionDiaria,
        OrdenTrabajo,
        PlanMantenimiento,
        ReporteFalla,
    )
    from apps.reportes.models import ReporteGenerado

    from .models import Maquina

    #hoy = timezone.localdate()
    hoy = date.today()
    en_7_dias = hoy + timedelta(days=7)

    conteo_estados = {
        fila["estado_operativo"]: fila["total"]
        for fila in Maquina.objects.values("estado_operativo").annotate(total=Count("pk"))
    }

    tarjetas = {
        "total_maquinas": Maquina.objects.count(),
        "operativas": conteo_estados.get("OPERATIVA", 0),
        "observadas": conteo_estados.get("OBSERVADA", 0),
        "paradas": conteo_estados.get("PARADA", 0),
        "mant_preventivo": conteo_estados.get("MANTENIMIENTO_PREVENTIVO", 0),
        "mant_correctivo": conteo_estados.get("MANTENIMIENTO_CORRECTIVO", 0),
        "fuera_servicio": conteo_estados.get("FUERA_DE_SERVICIO", 0),
        "ot_pendientes": OrdenTrabajo.objects.filter(
            estado_ot__in=["PENDIENTE", "PROGRAMADA", "EN_EJECUCION"]
        ).count(),
        "fallas_abiertas": ReporteFalla.objects.filter(
            estado_reporte__in=["ABIERTO", "EN_REVISION"]
        ).count(),
        "repuestos_bajo_stock": Repuesto.objects.filter(
            stock_actual__lte=F("stock_minimo")
        ).count(),
        "prox_mantenimientos": PlanMantenimiento.objects.filter(
            estado_plan="ACTIVO",
            fecha_proxima_ejecucion__range=[hoy, en_7_dias],
        ).count(),
        "reportes_semanales": ReporteGenerado.objects.filter(
            tipo_reporte="SEMANAL", descargable=True, estado__in=["GENERADO", "DESCARGADO"]
        ).count(),
    }

    repuestos_alerta = (
        Repuesto.objects.filter(stock_actual__lte=F("stock_minimo"))
        .select_related("id_proveedor")
        .order_by("stock_actual")[:10]
    )
    planes_vencidos = (
        PlanMantenimiento.objects.filter(
            estado_plan="ACTIVO", fecha_proxima_ejecucion__lt=hoy
        )
        .select_related("id_maquina")
        .order_by("fecha_proxima_ejecucion")[:10]
    )

    ultimas_observaciones = (
        ObservacionDiaria.objects.select_related("id_maquina", "id_usuario")
        .order_by("-fecha_hora")[:8]
    )
    ultimos_reportes_falla = (
        ReporteFalla.objects.select_related("id_maquina", "id_usuario_reporta")
        .order_by("-fecha_reporte")[:8]
    )
    ot_proximas = (
        OrdenTrabajo.objects.filter(
            estado_ot__in=["PENDIENTE", "PROGRAMADA", "EN_EJECUCION"]
        )
        .select_related("id_maquina", "responsable_tecnico")
        .order_by("fecha_programada")[:8]
    )
    maquinas_criticas = (
        Maquina.objects.filter(
            Q(criticidad__in=["ALTA", "MUY_ALTA"])
            | ~Q(estado_operativo="OPERATIVA")
        )
        .select_related("id_area")
        .order_by("-criticidad", "estado_operativo")[:8]
    )

    return {
        "tarjetas": tarjetas,
        "repuestos_alerta": repuestos_alerta,
        "planes_vencidos": planes_vencidos,
        "ultimas_observaciones": ultimas_observaciones,
        "ultimos_reportes_falla": ultimos_reportes_falla,
        "ot_proximas": ot_proximas,
        "maquinas_criticas": maquinas_criticas,
        "indicadores_resumen": _resumen_indicadores(),
        "hoy": hoy,
    }


def _resumen_indicadores():
    """Resumen ligero de indicadores (últimos 30 días) para la tarjeta del dashboard."""
    try:
        from apps.reportes.indicadores import resumen_dashboard

        return resumen_dashboard(dias=30)
    except Exception:
        return None
