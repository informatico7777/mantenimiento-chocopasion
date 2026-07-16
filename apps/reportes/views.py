"""Vistas de reportes PDF descargables."""
import os
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import rol_requerido
from apps.core.audit import registrar_auditoria
from apps.mantenimiento.services import generar_codigo

from .forms import ReportePeriodoForm
from .models import DetalleReporteGenerado, ReporteGenerado
from .pdf import render_pdf_bytes
from .services import recopilar_datos_periodo

PAGINATE_BY = 15


@login_required
def reporte_list(request):
    qs = ReporteGenerado.objects.select_related("id_area", "id_maquina", "generado_por")
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "reportes/list.html", {"page_obj": page})


@login_required
def reporte_semanal(request):
    """Formulario para generar el reporte (semanal por defecto: últimos 7 días)."""
    hoy = timezone.localdate()
    inicial = {
        "tipo_reporte": "SEMANAL",
        "fecha_inicio": hoy - timedelta(days=6),
        "fecha_fin": hoy,
    }
    form = ReportePeriodoForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        reporte = _generar_reporte(request, form.cleaned_data)
        messages.success(request, f"Reporte {reporte.codigo_reporte} generado correctamente.")
        return redirect("reportes:reporte_list")
    return render(request, "reportes/semanal.html", {"form": form})


@transaction.atomic
def _generar_reporte(request, datos):
    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]
    area = datos.get("id_area")
    maquina = datos.get("id_maquina")
    tipo = datos["tipo_reporte"]

    contenido = recopilar_datos_periodo(
        fecha_inicio, fecha_fin,
        id_area=area.pk if area else None,
        id_maquina=maquina.pk if maquina else None,
    )

    codigo = generar_codigo(ReporteGenerado, "codigo_reporte", "REP")
    titulo = f"Reporte {dict(ReportePeriodoForm.TIPO).get(tipo, tipo)} de mantenimiento"

    # 1) Crear primero el registro para obtener el código/ID.
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
        ruta_archivo="",  # se completa tras guardar el PDF
        descargable=True,
        resumen=_construir_resumen(contenido),
        estado="GENERADO",
    )

    # 2) Renderizar el PDF.
    contexto_pdf = {
        "reporte": reporte,
        "titulo": titulo,
        "planta": "Choco Pasión - Tingo María",
        "generado_por": request.user.nombre_completo,
        "fecha_generacion": timezone.now(),
        **contenido,
    }
    pdf_bytes = render_pdf_bytes("reportes/reporte_pdf.html", contexto_pdf)

    # 3) Guardar en media/reportes_pdf/.
    carpeta = os.path.join(settings.MEDIA_ROOT, "reportes_pdf")
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = f"{codigo}.pdf"
    ruta_absoluta = os.path.join(carpeta, nombre_archivo)
    with open(ruta_absoluta, "wb") as fh:
        fh.write(pdf_bytes)

    reporte.ruta_archivo = f"reportes_pdf/{nombre_archivo}"
    reporte.save(update_fields=["ruta_archivo"])

    # 4) Registrar los registros incluidos en detalle_reportes_generados.
    _registrar_detalles(reporte, contenido)

    registrar_auditoria(request, "reportes_generados", reporte.pk, "GENERAR_REPORTE",
                        f"Reporte {codigo} ({fecha_inicio} a {fecha_fin})")
    return reporte


def _construir_resumen(contenido):
    return (
        f"Checklists: {contenido['checklists'].count()} | "
        f"Observados/No aptos: {contenido['checklists_no_aptos'].count()} | "
        f"Observaciones: {contenido['observaciones'].count()} | "
        f"Fallas: {contenido['fallas'].count()} | "
        f"OT abiertas: {contenido['ot_abiertas'].count()} | "
        f"OT cerradas: {contenido['ot_cerradas'].count()} | "
        f"Repuestos bajo stock: {contenido['repuestos_bajo_stock'].count()}"
    )


def _registrar_detalles(reporte, contenido):
    mapa = [
        ("CHECKLIST", contenido["checklists"], "pk"),
        ("OBSERVACION", contenido["observaciones"], "pk"),
        ("FALLA", contenido["fallas"], "pk"),
        ("OT", contenido["ot_abiertas"], "pk"),
        ("OT", contenido["ot_cerradas"], "pk"),
        ("CONSUMO", contenido["consumos"], "pk"),
        ("REPUESTO", contenido["repuestos_bajo_stock"], "pk"),
    ]
    objetos = []
    for tipo, qs, _ in mapa:
        for obj in qs[:500]:
            objetos.append(DetalleReporteGenerado(
                id_reporte_generado=reporte,
                tipo_registro=tipo,
                id_registro=obj.pk,
                descripcion=str(obj)[:255],
            ))
    if objetos:
        DetalleReporteGenerado.objects.bulk_create(objetos)


@login_required
def reporte_descargar(request, pk):
    reporte = get_object_or_404(ReporteGenerado, pk=pk)
    ruta_absoluta = os.path.join(settings.MEDIA_ROOT, reporte.ruta_archivo)
    if not reporte.ruta_archivo or not os.path.exists(ruta_absoluta):
        raise Http404("El archivo del reporte no existe.")
    if reporte.estado == "GENERADO":
        reporte.estado = "DESCARGADO"
        reporte.save(update_fields=["estado"])
    registrar_auditoria(request, "reportes_generados", reporte.pk, "DESCARGAR",
                        f"Descarga de {reporte.codigo_reporte}")
    return FileResponse(
        open(ruta_absoluta, "rb"), as_attachment=True,
        filename=f"{reporte.codigo_reporte}.pdf",
    )


# =====================================================================
# MÓDULO DE INDICADORES DE MANTENIMIENTO
# =====================================================================
from decimal import Decimal  # noqa: E402

from django.http import HttpResponse  # noqa: E402
from django.urls import reverse  # noqa: E402

from apps.core.models import Area, Maquina  # noqa: E402

from . import indicadores as ind  # noqa: E402


def _parse_filtros_indicadores(request):
    #hoy = timezone.localdate()
    hoy = timezone.now().date()
    fi_str = request.GET.get("fecha_inicio")
    ff_str = request.GET.get("fecha_fin")
    try:
        fecha_inicio = (timezone.datetime.strptime(fi_str, "%Y-%m-%d").date()
                        if fi_str else hoy - timedelta(days=29))
    except ValueError:
        fecha_inicio = hoy - timedelta(days=29)
    try:
        fecha_fin = (timezone.datetime.strptime(ff_str, "%Y-%m-%d").date() if ff_str else hoy)
    except ValueError:
        fecha_fin = hoy
    if fecha_fin < fecha_inicio:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
    try:
        horas_jornada = Decimal(request.GET.get("horas_jornada") or "8")
        if horas_jornada <= 0:
            horas_jornada = Decimal("8")
    except (ValueError, ArithmeticError):
        horas_jornada = Decimal("8")
    f_area = request.GET.get("area", "")
    f_criticidad = request.GET.get("criticidad", "")
    f_estado = request.GET.get("estado", "")
    maquinas = Maquina.objects.select_related("id_area").all()
    if f_area:
        maquinas = maquinas.filter(id_area_id=f_area)
    if f_criticidad:
        maquinas = maquinas.filter(criticidad=f_criticidad)
    if f_estado:
        maquinas = maquinas.filter(estado_operativo=f_estado)
    filtros = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin,
               "horas_jornada": horas_jornada, "area": f_area,
               "criticidad": f_criticidad, "estado": f_estado}
    querystring = (f"fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
                   f"&horas_jornada={horas_jornada}&area={f_area}"
                   f"&criticidad={f_criticidad}&estado={f_estado}")
    return maquinas, fecha_inicio, fecha_fin, horas_jornada, filtros, querystring


@login_required
def indicadores_view(request):
    maquinas, fi, ff, hj, filtros, querystring = _parse_filtros_indicadores(request)
    resultados = ind.calcular_indicadores(maquinas, fi, ff, hj)
    contexto = {"resultados": resultados, "resumen": ind.construir_resumen(resultados),
                "rankings": ind.construir_rankings(resultados), "filtros": filtros,
                "querystring": querystring + "&", "areas": Area.objects.all(),
                "criticidades": Maquina._meta.get_field("criticidad").choices,
                "estados": Maquina._meta.get_field("estado_operativo").choices}
    return render(request, "reportes/indicadores.html", contexto)


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def indicador_calcular(request):
    maquinas, fi, ff, hj, filtros, querystring = _parse_filtros_indicadores(request)
    resultados = ind.calcular_indicadores(maquinas, fi, ff, hj)
    guardados = ind.guardar_indicadores(resultados, fi, ff)
    registrar_auditoria(request, "indicadores_mantenimiento", None, "GENERAR_REPORTE",
                        f"Calculo de indicadores {fi} a {ff} ({guardados} maquinas)")
    messages.success(request, f"Indicadores calculados y guardados para {guardados} maquina(s).")
    return redirect(f"{reverse('reportes:indicadores')}?{querystring}")


@login_required
def indicador_maquina_detalle(request, pk):
    maquina = get_object_or_404(Maquina.objects.select_related("id_area"), pk=pk)
    _, fi, ff, hj, filtros, querystring = _parse_filtros_indicadores(request)
    actual = ind.calcular_indicadores_maquina(maquina, fi, ff, hj)
    historicos = maquina.indicadores.order_by("-periodo_fin")[:20]
    return render(request, "reportes/indicadores_detalle.html",
                  {"maquina": maquina, "actual": actual, "filtros": filtros,
                   "historicos": historicos, "querystring": querystring + "&"})


@login_required
def indicador_exportar_pdf(request):
    maquinas, fi, ff, hj, filtros, _ = _parse_filtros_indicadores(request)
    resultados = ind.calcular_indicadores(maquinas, fi, ff, hj)
    contexto = {"resultados": resultados, "resumen": ind.construir_resumen(resultados),
                "rankings": ind.construir_rankings(resultados), "filtros": filtros,
                "planta": "Choco Pasion - Tingo Maria", "fecha_generacion": timezone.now()}
    pdf_bytes = render_pdf_bytes("reportes/indicadores_pdf.html", contexto)
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="indicadores_{fi}_{ff}.pdf"'
    return resp


@login_required
def indicador_exportar_excel(request):
    maquinas, fi, ff, hj, filtros, querystring = _parse_filtros_indicadores(request)
    resultados = ind.calcular_indicadores(maquinas, fi, ff, hj)
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        messages.error(request, "La exportacion a Excel requiere openpyxl.")
        return redirect(f"{reverse('reportes:indicadores')}?{querystring}")
    wb = Workbook(); ws = wb.active; ws.title = "Indicadores"
    ws.append(["Codigo", "Maquina", "Area", "Disp %", "Fallas", "MTBF", "MTTR",
               "Cumpl %", "Costo", "kWh"])
    for r in resultados:
        m = r["maquina"]
        ws.append([m.codigo_activo, m.nombre_maquina, m.id_area.nombre_area,
                   float(r["disponibilidad"]), r["numero_fallas"],
                   float(r["mtbf"]) if r["mtbf"] is not None else "-",
                   float(r["mttr"]) if r["mttr"] is not None else "-",
                   float(r["cumplimiento_preventivo"]) if r["cumplimiento_preventivo"] is not None else "-",
                   float(r["costo_total"]), float(r["consumo_kwh"])])
    resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = f'attachment; filename="indicadores_{fi}_{ff}.xlsx"'
    wb.save(resp)
    return resp
