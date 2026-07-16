"""Lógica de negocio del módulo de mantenimiento."""
from django.db import transaction
from django.db.models import Max
from django.utils import timezone


def generar_codigo(modelo, campo, prefijo):
    """
    Genera un código correlativo del tipo PREFIJO-AAAA-0001 basado en el año
    en curso y el último correlativo registrado para ese año.
    """
    #anio = timezone.localdate().year
    anio = timezone.now().date().year
    patron = f"{prefijo}-{anio}-"
    ultimo = (
        modelo.objects.filter(**{f"{campo}__startswith": patron})
        .aggregate(maximo=Max(campo))
        .get("maximo")
    )
    if ultimo:
        try:
            correlativo = int(ultimo.split("-")[-1]) + 1
        except (ValueError, IndexError):
            correlativo = 1
    else:
        correlativo = 1
    return f"{patron}{correlativo:04d}"


def evaluar_resultado_checklist(detalles):
    """
    Aplica la regla de negocio del checklist preoperacional:

    - Si algún ítem con bloquea_produccion=True NO cumple -> NO_APTA y
      permite_produccion=False.
    - Si hay incumplimientos no bloqueantes -> OBSERVADA, permite_produccion=True.
    - Si todo cumple -> APTA, permite_produccion=True.

    `detalles` es un iterable de tuplas (item_plantilla, cumple: bool).
    Devuelve (resultado_general, permite_produccion).
    """
    bloqueante_incumplido = False
    algun_incumplimiento = False
    for item, cumple in detalles:
        if not cumple:
            algun_incumplimiento = True
            if item.bloquea_produccion:
                bloqueante_incumplido = True
    if bloqueante_incumplido:
        return "NO_APTA", False
    if algun_incumplimiento:
        return "OBSERVADA", True
    return "APTA", True


@transaction.atomic
def convertir_falla_en_ot(reporte_falla, usuario, descripcion=None, tipo_ot="CORRECTIVA",
                          prioridad="ALTA"):
    """
    Crea una Orden de Trabajo a partir de un reporte de falla y actualiza el
    estado del reporte a CONVERTIDO_A_OT.
    """
    from .models import OrdenTrabajo

    codigo = generar_codigo(OrdenTrabajo, "codigo_ot", "OT")
    ot = OrdenTrabajo.objects.create(
        codigo_ot=codigo,
        id_maquina=reporte_falla.id_maquina,
        id_reporte_falla=reporte_falla,
        tipo_ot=tipo_ot,
        prioridad=prioridad,
        estado_ot="PENDIENTE",
        descripcion_trabajo=descripcion
        or f"Atención de falla {reporte_falla.codigo_reporte}: "
        f"{reporte_falla.descripcion_falla}",
    )
    reporte_falla.estado_reporte = "CONVERTIDO_A_OT"
    reporte_falla.save(update_fields=["estado_reporte"])
    return ot


@transaction.atomic
def convertir_observacion_en_falla(observacion, usuario):
    """Crea un reporte de falla a partir de una observación diaria crítica."""
    from .models import ReporteFalla

    codigo = generar_codigo(ReporteFalla, "codigo_reporte", "RF")
    reporte = ReporteFalla.objects.create(
        codigo_reporte=codigo,
        id_maquina=observacion.id_maquina,
        id_usuario_reporta_id=usuario.pk,
        turno=observacion.turno,
        sintoma=f"{observacion.get_tipo_observacion_display()} (observación diaria)",
        descripcion_falla=observacion.descripcion,
        nivel_urgencia=observacion.nivel_importancia,
        afecta_produccion=observacion.afecta_produccion,
        id_lote=observacion.id_lote,
        origen_reporte="OBSERVACION_DIARIA",
        estado_reporte="ABIERTO",
    )
    observacion.estado_observacion = "CONVERTIDA_A_OT"
    observacion.save(update_fields=["estado_observacion"])
    return reporte
