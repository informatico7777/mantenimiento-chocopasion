"""Vistas de reportes PDF descargables."""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.decorators import rol_requerido
from apps.core.audit import registrar_auditoria
from apps.core.models import Area, Maquina
from apps.mantenimiento.services import generar_codigo

from . import indicadores as ind
from .forms import ReportePeriodoForm
from .models import DetalleReporteGenerado, ReporteGenerado
from .pdf import render_pdf_bytes
from .services import recopilar_datos_periodo


PAGINATE_BY = 15


# =====================================================================
# REPORTES GENERADOS
# =====================================================================

@login_required
def reporte_list(request):
    """Lista los reportes generados."""

    qs = ReporteGenerado.objects.select_related(
        "id_area",
        "id_maquina",
        "generado_por",
    )

    page = Paginator(
        qs,
        PAGINATE_BY,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "reportes/list.html",
        {
            "page_obj": page,
        },
    )


@login_required
def reporte_semanal(request):
    """
    Muestra el formulario para generar reportes.

    De forma predeterminada, establece un periodo de siete días,
    contando el día actual.
    """

    # Se utiliza date.today() para evitar el error:
    # ValueError: localtime() cannot be applied to a naive datetime
    hoy = date.today()

    inicial = {
        "tipo_reporte": "SEMANAL",
        "fecha_inicio": hoy - timedelta(days=6),
        "fecha_fin": hoy,
    }

    form = ReportePeriodoForm(
        request.POST or None,
        initial=inicial,
    )

    if request.method == "POST" and form.is_valid():
        reporte = _generar_reporte(
            request,
            form.cleaned_data,
        )

        messages.success(
            request,
            f"Reporte {reporte.codigo_reporte} generado correctamente.",
        )

        return redirect("reportes:reporte_list")

    return render(
        request,
        "reportes/semanal.html",
        {
            "form": form,
        },
    )


@transaction.atomic
def _generar_reporte(request, datos):
    """Genera y registra un reporte de mantenimiento en PDF."""

    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]
    area = datos.get("id_area")
    maquina = datos.get("id_maquina")
    tipo = datos["tipo_reporte"]

    contenido = recopilar_datos_periodo(
        fecha_inicio,
        fecha_fin,
        id_area=area.pk if area else None,
        id_maquina=maquina.pk if maquina else None,
    )

    codigo = generar_codigo(
        ReporteGenerado,
        "codigo_reporte",
        "REP",
    )

    tipos_reporte = dict(ReportePeriodoForm.TIPO)

    titulo = (
        f"Reporte "
        f"{tipos_reporte.get(tipo, tipo)} "
        f"de mantenimiento"
    )

    # 1. Crear el registro para obtener el código y el ID.
    reporte = ReporteGenerado.objects.create(
        codigo_reporte=codigo,
        tipo_reporte=tipo,
        titulo_reporte=titulo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_area=area,
        id_maquina=maquina,
        generado_por_id=request.user.pk,
        formato="PDF",
        ruta_archivo="",
        descargable=True,
        resumen=_construir_resumen(contenido),
        estado="GENERADO",
    )

    # 2. Construir el contexto y renderizar el PDF.
    contexto_pdf = {
        "reporte": reporte,
        "titulo": titulo,
        "planta": "Choco Pasión - Tingo María",
        "generado_por": request.user.nombre_completo,
        "fecha_generacion": timezone.now(),
        **contenido,
    }

    pdf_bytes = render_pdf_bytes(
        "reportes/reporte_pdf.html",
        contexto_pdf,
    )

    # 3. Guardar el PDF en media/reportes_pdf/.
    carpeta = os.path.join(
        settings.MEDIA_ROOT,
        "reportes_pdf",
    )

    os.makedirs(
        carpeta,
        exist_ok=True,
    )

    nombre_archivo = f"{codigo}.pdf"

    ruta_absoluta = os.path.join(
        carpeta,
        nombre_archivo,
    )

    with open(ruta_absoluta, "wb") as archivo_pdf:
        archivo_pdf.write(pdf_bytes)

    reporte.ruta_archivo = f"reportes_pdf/{nombre_archivo}"

    reporte.save(
        update_fields=[
            "ruta_archivo",
        ],
    )

    # 4. Registrar los elementos incluidos en el reporte.
    _registrar_detalles(
        reporte,
        contenido,
    )

    registrar_auditoria(
        request,
        "reportes_generados",
        reporte.pk,
        "GENERAR_REPORTE",
        f"Reporte {codigo} ({fecha_inicio} a {fecha_fin})",
    )

    return reporte


def _construir_resumen(contenido):
    """Construye el resumen textual del reporte."""

    return (
        f"Checklists: {contenido['checklists'].count()} | "
        f"Observados/No aptos: "
        f"{contenido['checklists_no_aptos'].count()} | "
        f"Observaciones: {contenido['observaciones'].count()} | "
        f"Fallas: {contenido['fallas'].count()} | "
        f"OT abiertas: {contenido['ot_abiertas'].count()} | "
        f"OT cerradas: {contenido['ot_cerradas'].count()} | "
        f"Repuestos bajo stock: "
        f"{contenido['repuestos_bajo_stock'].count()}"
    )


def _registrar_detalles(reporte, contenido):
    """Registra los objetos incluidos en un reporte generado."""

    mapa = [
        (
            "CHECKLIST",
            contenido["checklists"],
        ),
        (
            "OBSERVACION",
            contenido["observaciones"],
        ),
        (
            "FALLA",
            contenido["fallas"],
        ),
        (
            "OT",
            contenido["ot_abiertas"],
        ),
        (
            "OT",
            contenido["ot_cerradas"],
        ),
        (
            "CONSUMO",
            contenido["consumos"],
        ),
        (
            "REPUESTO",
            contenido["repuestos_bajo_stock"],
        ),
    ]

    objetos = []

    for tipo_registro, queryset in mapa:
        for objeto in queryset[:500]:
            objetos.append(
                DetalleReporteGenerado(
                    id_reporte_generado=reporte,
                    tipo_registro=tipo_registro,
                    id_registro=objeto.pk,
                    descripcion=str(objeto)[:255],
                )
            )

    if objetos:
        DetalleReporteGenerado.objects.bulk_create(
            objetos,
        )


@login_required
def reporte_descargar(request, pk):
    """Descarga un reporte PDF previamente generado."""

    reporte = get_object_or_404(
        ReporteGenerado,
        pk=pk,
    )

    if not reporte.ruta_archivo:
        raise Http404(
            "El reporte no tiene un archivo asociado."
        )

    ruta_absoluta = os.path.join(
        settings.MEDIA_ROOT,
        reporte.ruta_archivo,
    )

    if not os.path.exists(ruta_absoluta):
        raise Http404(
            "El archivo del reporte no existe."
        )

    if reporte.estado == "GENERADO":
        reporte.estado = "DESCARGADO"

        reporte.save(
            update_fields=[
                "estado",
            ],
        )

    registrar_auditoria(
        request,
        "reportes_generados",
        reporte.pk,
        "DESCARGAR",
        f"Descarga de {reporte.codigo_reporte}",
    )

    return FileResponse(
        open(ruta_absoluta, "rb"),
        as_attachment=True,
        filename=f"{reporte.codigo_reporte}.pdf",
    )


# =====================================================================
# INDICADORES DE MANTENIMIENTO
# =====================================================================

def _parse_filtros_indicadores(request):
    """Procesa y valida los filtros de indicadores."""

    hoy = date.today()

    fecha_inicio_texto = request.GET.get(
        "fecha_inicio"
    )

    fecha_fin_texto = request.GET.get(
        "fecha_fin"
    )

    try:
        if fecha_inicio_texto:
            fecha_inicio = datetime.strptime(
                fecha_inicio_texto,
                "%Y-%m-%d",
            ).date()
        else:
            fecha_inicio = hoy - timedelta(days=29)

    except ValueError:
        fecha_inicio = hoy - timedelta(days=29)

    try:
        if fecha_fin_texto:
            fecha_fin = datetime.strptime(
                fecha_fin_texto,
                "%Y-%m-%d",
            ).date()
        else:
            fecha_fin = hoy

    except ValueError:
        fecha_fin = hoy

    if fecha_fin < fecha_inicio:
        fecha_inicio, fecha_fin = (
            fecha_fin,
            fecha_inicio,
        )

    try:
        horas_jornada = Decimal(
            request.GET.get("horas_jornada") or "8"
        )

        if horas_jornada <= 0:
            horas_jornada = Decimal("8")

    except (
        ValueError,
        ArithmeticError,
    ):
        horas_jornada = Decimal("8")

    filtro_area = request.GET.get(
        "area",
        "",
    )

    filtro_criticidad = request.GET.get(
        "criticidad",
        "",
    )

    filtro_estado = request.GET.get(
        "estado",
        "",
    )

    maquinas = Maquina.objects.select_related(
        "id_area"
    ).all()

    if filtro_area:
        maquinas = maquinas.filter(
            id_area_id=filtro_area
        )

    if filtro_criticidad:
        maquinas = maquinas.filter(
            criticidad=filtro_criticidad
        )

    if filtro_estado:
        maquinas = maquinas.filter(
            estado_operativo=filtro_estado
        )

    filtros = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "horas_jornada": horas_jornada,
        "area": filtro_area,
        "criticidad": filtro_criticidad,
        "estado": filtro_estado,
    }

    querystring = (
        f"fecha_inicio={fecha_inicio}"
        f"&fecha_fin={fecha_fin}"
        f"&horas_jornada={horas_jornada}"
        f"&area={filtro_area}"
        f"&criticidad={filtro_criticidad}"
        f"&estado={filtro_estado}"
    )

    return (
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
        filtros,
        querystring,
    )


@login_required
def indicadores_view(request):
    """Muestra el tablero de indicadores de mantenimiento."""

    (
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
        filtros,
        querystring,
    ) = _parse_filtros_indicadores(request)

    resultados = ind.calcular_indicadores(
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
    )

    contexto = {
        "resultados": resultados,
        "resumen": ind.construir_resumen(
            resultados
        ),
        "rankings": ind.construir_rankings(
            resultados
        ),
        "filtros": filtros,
        "querystring": querystring + "&",
        "areas": Area.objects.all(),
        "criticidades": (
            Maquina._meta.get_field(
                "criticidad"
            ).choices
        ),
        "estados": (
            Maquina._meta.get_field(
                "estado_operativo"
            ).choices
        ),
    }

    return render(
        request,
        "reportes/indicadores.html",
        contexto,
    )


@login_required
@rol_requerido(
    "JEFE_PRODUCCION",
    "TECNICO_MANTENIMIENTO",
)
def indicador_calcular(request):
    """Calcula y guarda los indicadores de mantenimiento."""

    (
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
        _,
        querystring,
    ) = _parse_filtros_indicadores(request)

    resultados = ind.calcular_indicadores(
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
    )

    guardados = ind.guardar_indicadores(
        resultados,
        fecha_inicio,
        fecha_fin,
    )

    registrar_auditoria(
        request,
        "indicadores_mantenimiento",
        None,
        "GENERAR_REPORTE",
        (
            f"Cálculo de indicadores "
            f"{fecha_inicio} a {fecha_fin} "
            f"({guardados} máquinas)"
        ),
    )

    messages.success(
        request,
        (
            f"Indicadores calculados y guardados "
            f"para {guardados} máquina(s)."
        ),
    )

    return redirect(
        f"{reverse('reportes:indicadores')}"
        f"?{querystring}"
    )


@login_required
def indicador_maquina_detalle(request, pk):
    """Muestra los indicadores de una máquina."""

    maquina = get_object_or_404(
        Maquina.objects.select_related(
            "id_area"
        ),
        pk=pk,
    )

    (
        _,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
        filtros,
        querystring,
    ) = _parse_filtros_indicadores(request)

    actual = ind.calcular_indicadores_maquina(
        maquina,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
    )

    historicos = maquina.indicadores.order_by(
        "-periodo_fin"
    )[:20]

    contexto = {
        "maquina": maquina,
        "actual": actual,
        "filtros": filtros,
        "historicos": historicos,
        "querystring": querystring + "&",
    }

    return render(
        request,
        "reportes/indicadores_detalle.html",
        contexto,
    )


@login_required
def indicador_exportar_pdf(request):
    """Exporta los indicadores de mantenimiento a PDF."""

    (
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
        filtros,
        _,
    ) = _parse_filtros_indicadores(request)

    resultados = ind.calcular_indicadores(
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
    )

    contexto = {
        "resultados": resultados,
        "resumen": ind.construir_resumen(
            resultados
        ),
        "rankings": ind.construir_rankings(
            resultados
        ),
        "filtros": filtros,
        "planta": "Choco Pasión - Tingo María",
        "fecha_generacion": timezone.now(),
    }

    pdf_bytes = render_pdf_bytes(
        "reportes/indicadores_pdf.html",
        contexto,
    )

    respuesta = HttpResponse(
        pdf_bytes,
        content_type="application/pdf",
    )

    respuesta["Content-Disposition"] = (
        f'attachment; '
        f'filename="indicadores_'
        f'{fecha_inicio}_{fecha_fin}.pdf"'
    )

    return respuesta


@login_required
def indicador_exportar_excel(request):
    """Exporta los indicadores de mantenimiento a Excel."""

    (
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
        _,
        querystring,
    ) = _parse_filtros_indicadores(request)

    resultados = ind.calcular_indicadores(
        maquinas,
        fecha_inicio,
        fecha_fin,
        horas_jornada,
    )

    try:
        from openpyxl import Workbook

    except ImportError:
        messages.error(
            request,
            "La exportación a Excel requiere openpyxl.",
        )

        return redirect(
            f"{reverse('reportes:indicadores')}"
            f"?{querystring}"
        )

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Indicadores"

    hoja.append(
        [
            "Código",
            "Máquina",
            "Área",
            "Disponibilidad %",
            "Fallas",
            "MTBF",
            "MTTR",
            "Cumplimiento %",
            "Costo",
            "kWh",
        ]
    )

    for resultado in resultados:
        maquina = resultado["maquina"]

        hoja.append(
            [
                maquina.codigo_activo,
                maquina.nombre_maquina,
                maquina.id_area.nombre_area,
                float(
                    resultado["disponibilidad"]
                ),
                resultado["numero_fallas"],
                (
                    float(resultado["mtbf"])
                    if resultado["mtbf"] is not None
                    else "-"
                ),
                (
                    float(resultado["mttr"])
                    if resultado["mttr"] is not None
                    else "-"
                ),
                (
                    float(
                        resultado[
                            "cumplimiento_preventivo"
                        ]
                    )
                    if resultado[
                        "cumplimiento_preventivo"
                    ] is not None
                    else "-"
                ),
                float(resultado["costo_total"]),
                float(resultado["consumo_kwh"]),
            ]
        )

    respuesta = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )

    respuesta["Content-Disposition"] = (
        f'attachment; '
        f'filename="indicadores_'
        f'{fecha_inicio}_{fecha_fin}.xlsx"'
    )

    libro.save(respuesta)

    return respuesta