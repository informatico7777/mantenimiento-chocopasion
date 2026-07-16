"""Vistas: checklist, observaciones, reportes de falla y órdenes de trabajo."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.decorators import rol_requerido
from apps.core.audit import registrar_auditoria
from apps.core.models import Maquina

from . import services
from .forms import (
    ChecklistEjecucionForm,
    ChecklistPlantillaForm,
    DetalleOrdenTrabajoForm,
    ObservacionDiariaForm,
    OrdenTrabajoForm,
    ReporteFallaForm,
)
from .models import (
    ChecklistDetalle,
    ChecklistEjecucion,
    ChecklistPlantilla,
    ObservacionDiaria,
    OrdenTrabajo,
    ReporteFalla,
)

PAGINATE_BY = 15


# ======================= CHECKLIST: PLANTILLAS =======================
@login_required
def checklist_plantillas(request):
    qs = ChecklistPlantilla.objects.select_related("id_maquina").order_by(
        "id_maquina", "orden_visualizacion"
    )
    f_maquina = request.GET.get("maquina", "")
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "checklist/plantillas.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(), "f_maquina": f_maquina,
    })


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def checklist_plantilla_crear(request):
    form = ChecklistPlantillaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        registrar_auditoria(request, "checklist_plantilla", item.pk, "CREAR", item.pregunta[:80])
        messages.success(request, "Ítem de checklist agregado.")
        return redirect("mantenimiento:checklist_plantillas")
    return render(request, "checklist/plantilla_form.html",
                  {"form": form, "titulo": "Nuevo ítem de checklist"})


# ======================= CHECKLIST: EJECUCIÓN =======================
@login_required
def checklist_list(request):
    qs = ChecklistEjecucion.objects.select_related("id_maquina", "id_usuario")
    f_maquina = request.GET.get("maquina", "")
    f_resultado = request.GET.get("resultado", "")
    f_fecha = request.GET.get("fecha", "")
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    if f_resultado:
        qs = qs.filter(resultado_general=f_resultado)
    if f_fecha:
        qs = qs.filter(fecha=f_fecha)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "checklist/list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(),
        "f_maquina": f_maquina, "f_resultado": f_resultado, "f_fecha": f_fecha,
    })


@login_required
def checklist_ejecutar(request, id_maquina):
    maquina = get_object_or_404(Maquina, pk=id_maquina)
    items = list(
        maquina.items_checklist.filter(estado="ACTIVO").order_by("orden_visualizacion")
    )
    form = ChecklistEjecucionForm(request.POST or None, initial={"fecha": timezone.now().date()})

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            resultados = []
            for item in items:
                # SI_NO / checkbox: marcado = cumple. Otros tipos: campo "cumple_X".
                cumple = request.POST.get(f"cumple_{item.pk}") == "1"
                resultados.append((item, cumple))

            resultado_general, permite = services.evaluar_resultado_checklist(resultados)

            ejecucion = form.save(commit=False)
            ejecucion.id_maquina = maquina
            ejecucion.id_usuario_id = request.user.pk
            ejecucion.resultado_general = resultado_general
            ejecucion.permite_produccion = permite
            ejecucion.save()

            for item in items:
                cumple = request.POST.get(f"cumple_{item.pk}") == "1"
                ChecklistDetalle.objects.create(
                    id_checklist=ejecucion,
                    id_item_checklist=item,
                    respuesta=request.POST.get(f"respuesta_{item.pk}", "") or None,
                    valor_medido=request.POST.get(f"valor_{item.pk}") or None,
                    cumple=cumple,
                    observacion=request.POST.get(f"obs_{item.pk}", "") or None,
                    requiere_ot=(not cumple and item.bloquea_produccion),
                    nivel_alerta="CRITICO" if (not cumple and item.bloquea_produccion)
                    else ("ALTO" if not cumple else "BAJO"),
                )

            # Regla de negocio: NO_APTA -> máquina observada, no permite producción.
            if resultado_general == "NO_APTA":
                from apps.core.views import _registrar_cambio_estado

                estado_previo = maquina.estado_operativo
                if maquina.estado_operativo == "OPERATIVA":
                    maquina.estado_operativo = "OBSERVADA"
                    maquina.save(update_fields=["estado_operativo"])
                    _registrar_cambio_estado(
                        request, maquina, estado_previo,
                        motivo=f"Checklist {ejecucion.fecha} resultó NO_APTA.",
                    )

            registrar_auditoria(
                request, "checklist_ejecucion", ejecucion.pk, "CREAR",
                f"Checklist {maquina.codigo_activo}: {resultado_general}",
            )

        if resultado_general == "NO_APTA":
            messages.error(
                request,
                "Checklist NO APTA. La máquina NO debe iniciar producción. "
                "Puede generar un reporte de falla desde el detalle.",
            )
        elif resultado_general == "OBSERVADA":
            messages.warning(request, "Checklist OBSERVADA. Revise los incumplimientos.")
        else:
            messages.success(request, "Checklist APTA. La máquina puede operar.")
        return redirect("mantenimiento:checklist_detalle", pk=ejecucion.pk)

    return render(request, "checklist/ejecutar.html",
                  {"maquina": maquina, "items": items, "form": form})


@login_required
def checklist_detalle(request, pk):
    ejecucion = get_object_or_404(
        ChecklistEjecucion.objects.select_related("id_maquina", "id_usuario"), pk=pk
    )
    detalles = ejecucion.detalles.select_related("id_item_checklist")
    return render(request, "checklist/detalle.html",
                  {"ejecucion": ejecucion, "detalles": detalles})


@login_required
def checklist_generar_falla(request, pk):
    """Genera un reporte de falla a partir de un checklist NO_APTA / OBSERVADA."""
    ejecucion = get_object_or_404(ChecklistEjecucion, pk=pk)
    if ejecucion.genero_reporte_falla:
        messages.info(request, "Este checklist ya generó un reporte de falla.")
        return redirect("mantenimiento:checklist_detalle", pk=pk)

    codigo = services.generar_codigo(ReporteFalla, "codigo_reporte", "RF")
    incumplidos = ejecucion.detalles.filter(cumple=False).select_related("id_item_checklist")
    descripcion = "Incumplimientos del checklist:\n" + "\n".join(
        f"- {d.id_item_checklist.pregunta}" for d in incumplidos
    ) if incumplidos else (ejecucion.observacion_general or "Checklist no apto.")

    reporte = ReporteFalla.objects.create(
        codigo_reporte=codigo,
        id_maquina=ejecucion.id_maquina,
        id_usuario_reporta_id=request.user.pk,
        turno=ejecucion.turno,
        sintoma="Checklist preoperacional no apto",
        descripcion_falla=descripcion,
        nivel_urgencia="ALTO",
        afecta_produccion=not ejecucion.permite_produccion,
        origen_reporte="CHECKLIST",
        estado_reporte="ABIERTO",
    )
    ejecucion.genero_reporte_falla = True
    ejecucion.save(update_fields=["genero_reporte_falla"])
    registrar_auditoria(request, "reportes_falla", reporte.pk, "CREAR",
                        f"Falla {codigo} desde checklist #{pk}")
    messages.success(request, f"Reporte de falla {codigo} generado.")
    return redirect("mantenimiento:falla_detalle", pk=reporte.pk)


# ======================= OBSERVACIONES DIARIAS =======================
@login_required
def observacion_list(request):
    qs = ObservacionDiaria.objects.select_related("id_maquina", "id_usuario")
    f_maquina = request.GET.get("maquina", "")
    f_tipo = request.GET.get("tipo", "")
    f_estado = request.GET.get("estado", "")
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    if f_tipo:
        qs = qs.filter(tipo_observacion=f_tipo)
    if f_estado:
        qs = qs.filter(estado_observacion=f_estado)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "observaciones/list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(),
        "tipos": ObservacionDiaria._meta.get_field("tipo_observacion").choices,
        "estados": ObservacionDiaria._meta.get_field("estado_observacion").choices,
        "f_maquina": f_maquina, "f_tipo": f_tipo, "f_estado": f_estado,
    })


@login_required
def observacion_crear(request):
    form = ObservacionDiariaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obs = form.save(commit=False)
        obs.id_usuario_id = request.user.pk
        obs.save()
        registrar_auditoria(request, "observaciones_diarias", obs.pk, "CREAR",
                            f"Observación {obs.tipo_observacion}")
        messages.success(request, "Observación registrada.")
        return redirect("mantenimiento:observacion_list")
    return render(request, "observaciones/form.html",
                  {"form": form, "titulo": "Nueva observación diaria"})


@login_required
def observacion_convertir_falla(request, pk):
    obs = get_object_or_404(ObservacionDiaria, pk=pk)
    reporte = services.convertir_observacion_en_falla(obs, request.user)
    registrar_auditoria(request, "reportes_falla", reporte.pk, "CREAR",
                        f"Falla {reporte.codigo_reporte} desde observación #{pk}")
    messages.success(request, f"Observación convertida en reporte de falla {reporte.codigo_reporte}.")
    return redirect("mantenimiento:falla_detalle", pk=reporte.pk)


# ======================= REPORTES DE FALLA =======================
@login_required
def falla_list(request):
    qs = ReporteFalla.objects.select_related("id_maquina", "id_usuario_reporta")
    f_maquina = request.GET.get("maquina", "")
    f_estado = request.GET.get("estado", "")
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    if f_estado:
        qs = qs.filter(estado_reporte=f_estado)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "fallas/list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(),
        "estados": ReporteFalla._meta.get_field("estado_reporte").choices,
        "f_maquina": f_maquina, "f_estado": f_estado,
    })


@login_required
def falla_crear(request):
    form = ReporteFallaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        falla = form.save(commit=False)
        falla.id_usuario_reporta_id = request.user.pk
        falla.codigo_reporte = services.generar_codigo(ReporteFalla, "codigo_reporte", "RF")
        falla.save()
        registrar_auditoria(request, "reportes_falla", falla.pk, "CREAR", falla.codigo_reporte)
        messages.success(request, f"Reporte de falla {falla.codigo_reporte} registrado.")
        return redirect("mantenimiento:falla_detalle", pk=falla.pk)
    return render(request, "fallas/form.html",
                  {"form": form, "titulo": "Nuevo reporte de falla"})


@login_required
def falla_detalle(request, pk):
    falla = get_object_or_404(
        ReporteFalla.objects.select_related("id_maquina", "id_usuario_reporta"), pk=pk
    )
    from apps.documentos.models import ArchivoAdjunto

    archivos = ArchivoAdjunto.objects.filter(
        tipo_entidad="FALLA", id_entidad=falla.pk, estado="ACTIVO"
    )
    return render(request, "fallas/detalle.html",
                  {"falla": falla, "archivos": archivos,
                   "ordenes": falla.ordenes.all()})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def falla_convertir_ot(request, pk):
    falla = get_object_or_404(ReporteFalla, pk=pk)
    if falla.estado_reporte == "CONVERTIDO_A_OT":
        messages.info(request, "Este reporte ya fue convertido en orden de trabajo.")
        return redirect("mantenimiento:falla_detalle", pk=pk)
    ot = services.convertir_falla_en_ot(falla, request.user)
    registrar_auditoria(request, "ordenes_trabajo", ot.pk, "CREAR",
                        f"OT {ot.codigo_ot} desde falla {falla.codigo_reporte}")
    messages.success(request, f"Orden de trabajo {ot.codigo_ot} creada.")
    return redirect("mantenimiento:ot_detalle", pk=ot.pk)


# ======================= ÓRDENES DE TRABAJO =======================
@login_required
def ot_list(request):
    qs = OrdenTrabajo.objects.select_related("id_maquina", "responsable_tecnico")
    f_maquina = request.GET.get("maquina", "")
    f_estado = request.GET.get("estado", "")
    f_tipo = request.GET.get("tipo", "")
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    if f_estado:
        qs = qs.filter(estado_ot=f_estado)
    if f_tipo:
        qs = qs.filter(tipo_ot=f_tipo)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "ordenes/list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(),
        "estados": OrdenTrabajo._meta.get_field("estado_ot").choices,
        "tipos": OrdenTrabajo._meta.get_field("tipo_ot").choices,
        "f_maquina": f_maquina, "f_estado": f_estado, "f_tipo": f_tipo,
    })


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def ot_crear(request):
    form = OrdenTrabajoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ot = form.save(commit=False)
        ot.codigo_ot = services.generar_codigo(OrdenTrabajo, "codigo_ot", "OT")
        ot.costo_total = (ot.costo_mano_obra or 0) + (ot.costo_repuestos or 0) + \
            (ot.costo_servicio_externo or 0)
        ot.save()
        registrar_auditoria(request, "ordenes_trabajo", ot.pk, "CREAR", ot.codigo_ot)
        messages.success(request, f"Orden de trabajo {ot.codigo_ot} creada.")
        return redirect("mantenimiento:ot_detalle", pk=ot.pk)
    return render(request, "ordenes/form.html",
                  {"form": form, "titulo": "Nueva orden de trabajo"})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def ot_editar(request, pk):
    ot = get_object_or_404(OrdenTrabajo, pk=pk)
    form = OrdenTrabajoForm(request.POST or None, instance=ot)
    if request.method == "POST" and form.is_valid():
        ot = form.save(commit=False)
        ot.costo_total = (ot.costo_mano_obra or 0) + (ot.costo_repuestos or 0) + \
            (ot.costo_servicio_externo or 0)
        ot.save()
        registrar_auditoria(request, "ordenes_trabajo", ot.pk, "EDITAR", ot.codigo_ot)
        messages.success(request, "Orden de trabajo actualizada.")
        return redirect("mantenimiento:ot_detalle", pk=ot.pk)
    return render(request, "ordenes/form.html",
                  {"form": form, "titulo": f"Editar OT {ot.codigo_ot}"})


@login_required
def ot_detalle(request, pk):
    ot = get_object_or_404(
        OrdenTrabajo.objects.select_related(
            "id_maquina", "responsable_tecnico", "id_reporte_falla"
        ),
        pk=pk,
    )
    detalle_form = DetalleOrdenTrabajoForm(request.POST or None)
    if request.method == "POST" and detalle_form.is_valid():
        det = detalle_form.save(commit=False)
        det.id_ot = ot
        det.save()
        registrar_auditoria(request, "detalle_orden_trabajo", det.pk, "CREAR",
                            f"Detalle OT {ot.codigo_ot}")
        messages.success(request, "Detalle de trabajo registrado.")
        return redirect("mantenimiento:ot_detalle", pk=ot.pk)

    from apps.documentos.models import ArchivoAdjunto

    archivos = ArchivoAdjunto.objects.filter(
        tipo_entidad="OT", id_entidad=ot.pk, estado="ACTIVO"
    )
    return render(request, "ordenes/detalle.html", {
        "ot": ot, "detalles": ot.detalles.all(), "detalle_form": detalle_form,
        "archivos": archivos,
    })
