"""Recopilación de datos para los reportes de mantenimiento."""
from django.db.models import F


def recopilar_datos_periodo(fecha_inicio, fecha_fin, id_area=None, id_maquina=None):
    """
    Devuelve un diccionario con los conjuntos de datos del periodo solicitado,
    listos para alimentar el reporte semanal/diario/mensual en PDF.
    """
    from apps.inventario.models import MovimientoRepuesto, Repuesto
    from apps.mantenimiento.models import (
        ChecklistDetalle,
        ChecklistEjecucion,
        ObservacionDiaria,
        OrdenTrabajo,
        ReporteFalla,
    )
    from apps.produccion.models import ConsumoEnergetico

    def filtrar_maquina(qs, campo="id_maquina"):
        if id_area:
            qs = qs.filter(**{f"{campo}__id_area_id": id_area})
        if id_maquina:
            qs = qs.filter(**{f"{campo}_id": id_maquina})
        return qs

    checklists = filtrar_maquina(
        ChecklistEjecucion.objects.select_related("id_maquina", "id_usuario").filter(
            fecha__range=[fecha_inicio, fecha_fin]
        )
    ).order_by("fecha")

    incumplimientos = ChecklistDetalle.objects.select_related(
        "id_checklist__id_maquina", "id_item_checklist"
    ).filter(
        id_checklist__fecha__range=[fecha_inicio, fecha_fin], cumple=False
    )
    if id_area:
        incumplimientos = incumplimientos.filter(
            id_checklist__id_maquina__id_area_id=id_area
        )
    if id_maquina:
        incumplimientos = incumplimientos.filter(id_checklist__id_maquina_id=id_maquina)

    observaciones = filtrar_maquina(
        ObservacionDiaria.objects.select_related("id_maquina", "id_usuario").filter(
            fecha_hora__date__range=[fecha_inicio, fecha_fin]
        )
    ).order_by("fecha_hora")

    fallas = filtrar_maquina(
        ReporteFalla.objects.select_related("id_maquina", "id_usuario_reporta").filter(
            fecha_reporte__date__range=[fecha_inicio, fecha_fin]
        )
    ).order_by("fecha_reporte")

    ot_base = filtrar_maquina(
        OrdenTrabajo.objects.select_related("id_maquina", "responsable_tecnico").filter(
            fecha_creacion__date__range=[fecha_inicio, fecha_fin]
        )
    )
    ot_abiertas = ot_base.exclude(estado_ot__in=["CERRADA", "CANCELADA"]).order_by(
        "fecha_programada"
    )
    ot_cerradas = ot_base.filter(estado_ot="CERRADA").order_by("-fecha_fin_real")

    checklists_no_aptos = checklists.filter(
        resultado_general__in=["OBSERVADA", "NO_APTA"]
    )

    movimientos_salida = MovimientoRepuesto.objects.select_related("id_repuesto").filter(
        fecha_movimiento__date__range=[fecha_inicio, fecha_fin],
        tipo_movimiento__in=["SALIDA", "AJUSTE_NEGATIVO"],
    ).order_by("-fecha_movimiento")

    repuestos_bajo_stock = Repuesto.objects.filter(
        stock_actual__lte=F("stock_minimo")
    ).select_related("id_proveedor")

    consumos = filtrar_maquina(
        ConsumoEnergetico.objects.select_related("id_maquina").filter(
            fecha__range=[fecha_inicio, fecha_fin]
        )
    ).order_by("fecha")

    return {
        "checklists": checklists,
        "checklists_no_aptos": checklists_no_aptos,
        "incumplimientos": incumplimientos,
        "observaciones": observaciones,
        "fallas": fallas,
        "ot_abiertas": ot_abiertas,
        "ot_cerradas": ot_cerradas,
        "movimientos_salida": movimientos_salida,
        "repuestos_bajo_stock": repuestos_bajo_stock,
        "consumos": consumos,
    }
