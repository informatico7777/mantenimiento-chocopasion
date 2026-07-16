"""
Módulo de cálculo de indicadores de mantenimiento.

Toda la lógica de cálculo vive aquí (separada de las vistas). Las vistas solo
orquestan: leen filtros, llaman a estas funciones y arman el contexto.

Indicadores:
  - Disponibilidad (%)   = ((H. programadas - H. parada) / H. programadas) * 100
  - MTBF (h)             = Horas de operación / N.º de fallas
  - MTTR (h)             = Tiempo total de reparación / N.º de reparaciones
  - Cumplimiento prev.(%)= (OT preventivas cerradas / OT preventivas programadas) * 100
  - Costo mantenimiento  = mano de obra + repuestos + servicio externo (costo_total OT)
  - Consumo energético   = suma de kWh estimados de consumo_energetico

Convenciones / supuestos (documentados):
  - "Horas programadas" = días del periodo x horas de jornada (por defecto 8 h/día).
    Es configurable por la vista (parámetro horas_jornada) porque la BD no tiene
    un calendario de turnos.
  - Las OT se asignan al periodo por su fecha de creación (fecha_creacion).
  - "Reparaciones" (para MTTR) = OT correctivas CERRADAS dentro del periodo.
  - "N.º de fallas" (para MTBF) = reportes_falla del periodo (fecha_reporte).
  - Disponibilidad y cumplimiento se acotan a [0, 100] para respetar los CHECK
    de la tabla indicadores_mantenimiento.

NINGUNA función aquí altera tablas de negocio salvo `guardar_indicadores`, que
solo escribe en `indicadores_mantenimiento` mediante update_or_create sobre la
clave única (id_maquina, periodo_inicio, periodo_fin).
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

CERO = Decimal("0")
HORAS_JORNADA_DEFECTO = Decimal("8")

_DEC = DecimalField(max_digits=18, decimal_places=2)


def _dec(valor):
    """Convierte a Decimal de forma segura."""
    if valor is None:
        return CERO
    return Decimal(str(valor))


def _q2(valor):
    """Redondea a 2 decimales."""
    return _dec(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _clamp(valor, minimo=CERO, maximo=Decimal("100")):
    valor = _dec(valor)
    if valor < minimo:
        return minimo
    if valor > maximo:
        return maximo
    return valor


def _suma(qs, campo):
    return qs.aggregate(s=Coalesce(Sum(campo), Value(0, output_field=_DEC), output_field=_DEC))["s"]


def calcular_indicadores_maquina(maquina, fecha_inicio, fecha_fin,
                                 horas_jornada=HORAS_JORNADA_DEFECTO):
    """
    Calcula (sin guardar) los indicadores de una máquina para el periodo dado.
    Devuelve un diccionario con todos los valores listos para mostrar/guardar.
    """
    from apps.mantenimiento.models import OrdenTrabajo, ReporteFalla
    from apps.produccion.models import ConsumoEnergetico

    horas_jornada = _dec(horas_jornada)
    dias = (fecha_fin - fecha_inicio).days + 1
    if dias < 1:
        dias = 1
    horas_programadas = Decimal(dias) * horas_jornada

    # --- Órdenes de trabajo del periodo (por fecha de creación) ---
    ot_periodo = OrdenTrabajo.objects.filter(
        id_maquina=maquina, fecha_creacion__date__range=[fecha_inicio, fecha_fin]
    )

    horas_parada = _suma(ot_periodo, "tiempo_parada_horas")
    horas_operacion = horas_programadas - horas_parada
    if horas_operacion < CERO:
        horas_operacion = CERO

    # --- Disponibilidad ---
    if horas_programadas > CERO:
        disponibilidad = (horas_operacion / horas_programadas) * Decimal("100")
    else:
        disponibilidad = CERO
    disponibilidad = _clamp(disponibilidad)

    # --- Fallas y MTBF ---
    numero_fallas = ReporteFalla.objects.filter(
        id_maquina=maquina, fecha_reporte__date__range=[fecha_inicio, fecha_fin]
    ).count()
    mtbf = (horas_operacion / Decimal(numero_fallas)) if numero_fallas > 0 else None

    # --- Reparaciones (correctivas cerradas) y MTTR ---
    correctivas_cerradas = ot_periodo.filter(tipo_ot="CORRECTIVA", estado_ot="CERRADA")
    num_reparaciones = correctivas_cerradas.count()
    tiempo_reparacion = _suma(correctivas_cerradas, "tiempo_parada_horas")
    mttr = (tiempo_reparacion / Decimal(num_reparaciones)) if num_reparaciones > 0 else None

    # --- Cumplimiento preventivo ---
    preventivas = ot_periodo.filter(tipo_ot="PREVENTIVA")
    prev_programadas = preventivas.count()
    prev_cerradas = preventivas.filter(estado_ot="CERRADA").count()
    if prev_programadas > 0:
        cumplimiento = _clamp(Decimal(prev_cerradas) / Decimal(prev_programadas) * Decimal("100"))
    else:
        cumplimiento = None

    # --- Costos ---
    costo_mano_obra = _suma(ot_periodo, "costo_mano_obra")
    costo_repuestos = _suma(ot_periodo, "costo_repuestos")
    costo_servicio = _suma(ot_periodo, "costo_servicio_externo")
    costo_total = _suma(ot_periodo, "costo_total")
    # Respaldo: si costo_total viene en 0 pero hay componentes, recalcular.
    if costo_total == CERO:
        costo_total = costo_mano_obra + costo_repuestos + costo_servicio

    # --- Consumo energético ---
    consumo = ConsumoEnergetico.objects.filter(
        id_maquina=maquina, fecha__range=[fecha_inicio, fecha_fin]
    )
    consumo_kwh = _suma(consumo, "kwh_estimado")
    consumo_costo = _suma(consumo, "costo_total_energia")

    return {
        "maquina": maquina,
        "horas_programadas": _q2(horas_programadas),
        "horas_parada": _q2(horas_parada),
        "horas_operacion": _q2(horas_operacion),
        "disponibilidad": _q2(disponibilidad),
        "numero_fallas": numero_fallas,
        "mtbf": _q2(mtbf) if mtbf is not None else None,
        "mttr": _q2(mttr) if mttr is not None else None,
        "num_reparaciones": num_reparaciones,
        "cumplimiento_preventivo": _q2(cumplimiento) if cumplimiento is not None else None,
        "prev_programadas": prev_programadas,
        "prev_cerradas": prev_cerradas,
        "costo_mano_obra": _q2(costo_mano_obra),
        "costo_repuestos": _q2(costo_repuestos),
        "costo_servicio_externo": _q2(costo_servicio),
        "costo_total": _q2(costo_total),
        "consumo_kwh": _q2(consumo_kwh),
        "consumo_costo": _q2(consumo_costo),
    }


def calcular_indicadores(maquinas, fecha_inicio, fecha_fin,
                         horas_jornada=HORAS_JORNADA_DEFECTO):
    """Calcula los indicadores para un conjunto de máquinas. Devuelve lista de dicts."""
    return [
        calcular_indicadores_maquina(m, fecha_inicio, fecha_fin, horas_jornada)
        for m in maquinas
    ]


def construir_resumen(resultados):
    """Agrega los resultados para las tarjetas resumen."""
    n = len(resultados)
    if n == 0:
        return {
            "n_maquinas": 0, "disponibilidad_promedio": CERO, "total_fallas": 0,
            "costo_total": CERO, "horas_parada_total": CERO, "consumo_total_kwh": CERO,
            "mtbf_promedio": None, "mttr_promedio": None,
        }
    disp = sum((r["disponibilidad"] for r in resultados), CERO) / Decimal(n)
    mtbf_vals = [r["mtbf"] for r in resultados if r["mtbf"] is not None]
    mttr_vals = [r["mttr"] for r in resultados if r["mttr"] is not None]
    return {
        "n_maquinas": n,
        "disponibilidad_promedio": _q2(disp),
        "total_fallas": sum(r["numero_fallas"] for r in resultados),
        "costo_total": _q2(sum((r["costo_total"] for r in resultados), CERO)),
        "horas_parada_total": _q2(sum((r["horas_parada"] for r in resultados), CERO)),
        "consumo_total_kwh": _q2(sum((r["consumo_kwh"] for r in resultados), CERO)),
        "mtbf_promedio": _q2(sum(mtbf_vals, CERO) / Decimal(len(mtbf_vals))) if mtbf_vals else None,
        "mttr_promedio": _q2(sum(mttr_vals, CERO) / Decimal(len(mttr_vals))) if mttr_vals else None,
    }


def construir_rankings(resultados, top=5):
    """Devuelve los rankings solicitados (top N)."""
    return {
        "peor_disponibilidad": sorted(resultados, key=lambda r: r["disponibilidad"])[:top],
        "mas_fallas": sorted(resultados, key=lambda r: r["numero_fallas"], reverse=True)[:top],
        "mayor_costo": sorted(resultados, key=lambda r: r["costo_total"], reverse=True)[:top],
        "mayor_parada": sorted(resultados, key=lambda r: r["horas_parada"], reverse=True)[:top],
    }


def guardar_indicadores(resultados, fecha_inicio, fecha_fin):
    """
    Persiste los resultados en `indicadores_mantenimiento` usando la clave única
    (id_maquina, periodo_inicio, periodo_fin). Devuelve la cantidad guardada.
    No toca ninguna otra tabla.
    """
    from .models import IndicadorMantenimiento

    guardados = 0
    for r in resultados:
        IndicadorMantenimiento.objects.update_or_create(
            id_maquina=r["maquina"],
            periodo_inicio=fecha_inicio,
            periodo_fin=fecha_fin,
            defaults={
                "horas_programadas": r["horas_programadas"],
                "horas_parada": r["horas_parada"],
                "disponibilidad_porcentaje": r["disponibilidad"],
                "numero_fallas": r["numero_fallas"],
                "mtbf_horas": r["mtbf"],
                "mttr_horas": r["mttr"],
                "cumplimiento_preventivo": r["cumplimiento_preventivo"],
                "costo_mantenimiento": r["costo_total"],
                "consumo_energia_total": r["consumo_kwh"],
                "observacion": "Calculado automáticamente desde las tablas operativas.",
            },
        )
        guardados += 1
    return guardados


def resumen_dashboard(dias=30, horas_jornada=HORAS_JORNADA_DEFECTO):
    """
    Resumen ligero para la tarjeta del dashboard: disponibilidad promedio,
    total de fallas y costo de mantenimiento de los últimos `dias` días.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.core.models import Maquina

    fin = timezone.localdate()
    inicio = fin - timedelta(days=dias - 1)
    maquinas = Maquina.objects.all()
    resultados = calcular_indicadores(maquinas, inicio, fin, horas_jornada)
    resumen = construir_resumen(resultados)
    resumen["periodo_inicio"] = inicio
    resumen["periodo_fin"] = fin
    return resumen
