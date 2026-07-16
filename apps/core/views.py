"""Vistas del núcleo: dashboard, áreas y máquinas."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import rol_requerido
from apps.core.audit import registrar_auditoria

from .dashboard import construir_contexto_dashboard
from .forms import AreaForm, MaquinaForm
from .models import Area, Maquina

PAGINATE_BY = 15


@login_required
def dashboard(request):
    contexto = construir_contexto_dashboard()
    return render(request, "dashboard.html", contexto)


# ----------------------------- ÁREAS -----------------------------
@login_required
def area_list(request):
    qs = Area.objects.annotate(num_maquinas=Count("maquinas")).order_by("nombre_area")
    buscar = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()
    if buscar:
        qs = qs.filter(nombre_area__icontains=buscar)
    if estado:
        qs = qs.filter(estado=estado)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "areas/list.html", {"page_obj": page, "q": buscar, "estado": estado})


@login_required
@rol_requerido("JEFE_PRODUCCION")
def area_crear(request):
    form = AreaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        area = form.save()
        registrar_auditoria(request, "areas", area.pk, "CREAR", f"Área {area.nombre_area}")
        messages.success(request, "Área creada correctamente.")
        return redirect("core:area_list")
    return render(request, "areas/form.html", {"form": form, "titulo": "Nueva área"})


@login_required
@rol_requerido("JEFE_PRODUCCION")
def area_editar(request, pk):
    area = get_object_or_404(Area, pk=pk)
    form = AreaForm(request.POST or None, instance=area)
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar_auditoria(request, "areas", area.pk, "EDITAR", f"Área {area.nombre_area}")
        messages.success(request, "Área actualizada.")
        return redirect("core:area_list")
    return render(request, "areas/form.html", {"form": form, "titulo": "Editar área"})


@login_required
@rol_requerido("JEFE_PRODUCCION")
def area_toggle(request, pk):
    area = get_object_or_404(Area, pk=pk)
    area.estado = "INACTIVA" if area.estado == "ACTIVA" else "ACTIVA"
    area.save(update_fields=["estado"])
    registrar_auditoria(request, "areas", area.pk, "EDITAR", f"Estado -> {area.estado}")
    messages.info(request, f"Área {area.nombre_area}: {area.estado}.")
    return redirect("core:area_list")


# ---------------------------- MÁQUINAS ----------------------------
@login_required
def maquina_list(request):
    qs = Maquina.objects.select_related("id_area", "responsable_maquina").all()
    f_area = request.GET.get("area", "")
    f_criticidad = request.GET.get("criticidad", "")
    f_estado = request.GET.get("estado", "")
    buscar = request.GET.get("q", "").strip()
    if f_area:
        qs = qs.filter(id_area_id=f_area)
    if f_criticidad:
        qs = qs.filter(criticidad=f_criticidad)
    if f_estado:
        qs = qs.filter(estado_operativo=f_estado)
    if buscar:
        qs = qs.filter(
            Q(nombre_maquina__icontains=buscar) | Q(codigo_activo__icontains=buscar)
        )
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    contexto = {
        "page_obj": page,
        "areas": Area.objects.all(),
        "criticidades": Maquina._meta.get_field("criticidad").choices,
        "estados": Maquina._meta.get_field("estado_operativo").choices,
        "f_area": f_area,
        "f_criticidad": f_criticidad,
        "f_estado": f_estado,
        "q": buscar,
    }
    return render(request, "maquinas/list.html", contexto)


@login_required
def maquina_detalle(request, pk):
    maquina = get_object_or_404(
        Maquina.objects.select_related("id_area", "responsable_maquina"), pk=pk
    )
    from apps.documentos.models import ArchivoAdjunto
    from apps.core.services import analizar_activos_maquina

    # Análisis integral: componentes (con prioridad preventiva), fallas
    # probables, repuestos críticos y banderas de alerta.
    activos = analizar_activos_maquina(maquina)

    contexto = {
        "maquina": maquina,
        "componentes": activos["componentes"],
        "fallas_probables": activos["fallas_probables"],
        "repuestos_criticos": activos["repuestos_criticos"],
        "componentes_danados": activos["componentes_danados"],
        "fallas_riesgo_alto": activos["fallas_riesgo_alto"],
        "fallas_criticas": activos["fallas_criticas"],
        "fallas_altas": activos["fallas_altas"],
        "repuestos_bajo_stock": activos["repuestos_bajo_stock"],
        "hay_stock_bajo": activos["hay_stock_bajo"],
        "items_checklist": maquina.items_checklist.filter(estado="ACTIVO"),
        "observaciones": maquina.observaciones_diarias.select_related("id_usuario")
        .order_by("-fecha_hora")[:10],
        "reportes_falla": maquina.reportes_falla.order_by("-fecha_reporte")[:10],
        "ordenes": maquina.ordenes.order_by("-fecha_creacion")[:10],
        "repuestos": maquina.repuestos_asociados.select_related("id_repuesto"),
        "consumos": maquina.consumos.order_by("-fecha")[:10],
        "historial": maquina.historial_estados.select_related("id_usuario")[:15],
        "funciones": maquina.funciones.select_related("id_funcion"),
        "archivos": ArchivoAdjunto.objects.filter(
            tipo_entidad="MAQUINA", id_entidad=maquina.pk, estado="ACTIVO"
        ),
    }
    return render(request, "maquinas/detalle.html", contexto)


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def maquina_crear(request):
    form = MaquinaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        maquina = form.save()
        registrar_auditoria(
            request, "maquinas", maquina.pk, "CREAR", f"Máquina {maquina.codigo_activo}"
        )
        messages.success(request, "Máquina registrada correctamente.")
        return redirect("core:maquina_detalle", pk=maquina.pk)
    return render(request, "maquinas/form.html", {"form": form, "titulo": "Nueva máquina"})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def maquina_editar(request, pk):
    maquina = get_object_or_404(Maquina, pk=pk)
    estado_previo = maquina.estado_operativo
    form = MaquinaForm(request.POST or None, instance=maquina)
    if request.method == "POST" and form.is_valid():
        maquina = form.save()
        # Registrar cambio de estado en el historial si corresponde.
        if maquina.estado_operativo != estado_previo:
            _registrar_cambio_estado(request, maquina, estado_previo)
        registrar_auditoria(
            request, "maquinas", maquina.pk, "EDITAR", f"Máquina {maquina.codigo_activo}"
        )
        messages.success(request, "Máquina actualizada.")
        return redirect("core:maquina_detalle", pk=maquina.pk)
    return render(request, "maquinas/form.html", {"form": form, "titulo": "Editar máquina"})


def _registrar_cambio_estado(request, maquina, estado_previo, motivo="", id_ot=None):
    """Inserta un registro en historial_estado_maquina."""
    from .models import HistorialEstadoMaquina

    HistorialEstadoMaquina.objects.create(
        id_maquina=maquina,
        estado_anterior=estado_previo,
        estado_nuevo=maquina.estado_operativo,
        motivo_cambio=motivo or "Cambio de estado desde edición de máquina.",
        id_usuario_id=request.user.pk,
        id_ot_id=id_ot,
    )


# =====================================================================
# MÓDULO DE AUDITORÍA DEL SISTEMA (solo ADMINISTRADOR)
# Lectura de la tabla auditoria_sistema. La escritura la hace el helper
# registrar_auditoria (apps/core/audit.py), ya usado en todo el proyecto.
# =====================================================================
from apps.core import auditoria as aud  # noqa: E402
from apps.core import services as aud_services  # noqa: E402
from apps.core.forms import AuditoriaFiltroForm  # noqa: E402


def _querystring_sin_page(request):
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


@login_required
@rol_requerido()  # sin roles extra => solo ADMINISTRADOR
def auditoria_list(request):
    form = AuditoriaFiltroForm(request.GET or None)
    filtros = form.cleaned_data if form.is_valid() else {}
    qs = aud.filtrar_auditoria(filtros)

    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    for evento in page:
        evento.badge = aud.badge_accion(evento.accion)

    qstring = _querystring_sin_page(request)
    contexto = {
        "form": form,
        "page_obj": page,
        "total": qs.count(),
        "querystring": (qstring + "&") if qstring else "",
    }
    return render(request, "core/auditoria_list.html", contexto)


@login_required
@rol_requerido()
def auditoria_detalle(request, pk):
    from apps.reportes.models import AuditoriaSistema

    evento = get_object_or_404(
        AuditoriaSistema.objects.select_related("id_usuario"), pk=pk
    )
    evento.badge = aud.badge_accion(evento.accion)
    return render(request, "core/auditoria_detalle.html", {"evento": evento})


@login_required
@rol_requerido()
def auditoria_exportar_excel(request):
    form = AuditoriaFiltroForm(request.GET or None)
    filtros = form.cleaned_data if form.is_valid() else {}
    qs = aud.filtrar_auditoria(filtros)
    resp = aud_services.exportar_auditoria_excel(qs, filename="auditoria.xlsx")
    if resp is None:
        messages.error(request, "La exportación a Excel requiere openpyxl (pip install openpyxl).")
        return redirect("core:auditoria_list")
    registrar_auditoria(request, "auditoria_sistema", None, "DESCARGAR",
                        "Exportación de auditoría a Excel")
    return resp


@login_required
@rol_requerido()
def auditoria_exportar_pdf(request):
    form = AuditoriaFiltroForm(request.GET or None)
    filtros = form.cleaned_data if form.is_valid() else {}
    qs = aud.filtrar_auditoria(filtros)
    resp = aud_services.exportar_auditoria_pdf(qs, filtros, filename="auditoria.pdf")
    registrar_auditoria(request, "auditoria_sistema", None, "DESCARGAR",
                        "Exportación de auditoría a PDF")
    return resp


# =====================================================================
# CRUD de COMPONENTES DE MÁQUINA y FALLAS PROBABLES
# Crear/editar/eliminar: ADMINISTRADOR, JEFE_PRODUCCION, TECNICO_MANTENIMIENTO
# Listar/ver detalle: cualquier usuario autenticado (incluye OPERADOR).
# =====================================================================
from apps.core.forms import (  # noqa: E402
    ComponenteMaquinaForm,
    FallaProbableForm,
    combinar_riesgo,
    sugerir_nivel_riesgo,
)
from apps.core.models import ComponenteMaquina, FallaProbable  # noqa: E402

GESTORES_ACTIVOS = ("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")


# ------------------------- COMPONENTES -------------------------
@login_required
def componente_list(request):
    qs = ComponenteMaquina.objects.select_related("id_maquina", "id_maquina__id_area")
    f_maquina = request.GET.get("maquina", "")
    f_criticidad = request.GET.get("criticidad", "")
    f_estado = request.GET.get("estado", "")
    buscar = request.GET.get("q", "").strip()
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    if f_criticidad:
        qs = qs.filter(criticidad_componente=f_criticidad)
    if f_estado:
        qs = qs.filter(estado_componente=f_estado)
    if buscar:
        qs = qs.filter(nombre_componente__icontains=buscar)
    page = Paginator(qs.order_by("id_maquina", "nombre_componente"), PAGINATE_BY).get_page(
        request.GET.get("page")
    )
    return render(request, "core/componentes_list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(),
        "criticidades": ComponenteMaquina._meta.get_field("criticidad_componente").choices,
        "estados": ComponenteMaquina._meta.get_field("estado_componente").choices,
        "f_maquina": f_maquina, "f_criticidad": f_criticidad, "f_estado": f_estado, "q": buscar,
    })


@login_required
def componente_detalle(request, pk):
    componente = get_object_or_404(
        ComponenteMaquina.objects.select_related("id_maquina"), pk=pk
    )
    fallas = componente.fallas_probables.all()
    return render(request, "core/componentes_detalle.html",
                  {"componente": componente, "fallas": fallas})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def componente_crear(request, id_maquina=None):
    maquina = get_object_or_404(Maquina, pk=id_maquina) if id_maquina else None
    form = ComponenteMaquinaForm(request.POST or None, maquina=maquina)
    if request.method == "POST" and form.is_valid():
        comp = form.save(commit=False)
        if maquina is not None:
            comp.id_maquina = maquina
        comp.save()
        registrar_auditoria(request, "componentes_maquina", comp.pk, "CREAR",
                            f"Componente {comp.nombre_componente} ({comp.id_maquina.codigo_activo})")
        messages.success(request, "Componente registrado correctamente.")
        if maquina is not None:
            return redirect("core:maquina_detalle", pk=maquina.pk)
        return redirect("core:componente_detalle", pk=comp.pk)
    return render(request, "core/componentes_form.html",
                  {"form": form, "titulo": "Nuevo componente", "maquina": maquina})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def componente_editar(request, pk):
    comp = get_object_or_404(ComponenteMaquina, pk=pk)
    form = ComponenteMaquinaForm(request.POST or None, instance=comp)
    if request.method == "POST" and form.is_valid():
        comp = form.save()
        registrar_auditoria(request, "componentes_maquina", comp.pk, "EDITAR",
                            f"Componente {comp.nombre_componente}")
        messages.success(request, "Componente actualizado.")
        return redirect("core:componente_detalle", pk=comp.pk)
    return render(request, "core/componentes_form.html",
                  {"form": form, "titulo": f"Editar {comp.nombre_componente}", "maquina": comp.id_maquina})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def componente_cambiar_estado(request, pk):
    comp = get_object_or_404(ComponenteMaquina, pk=pk)
    if request.method == "POST":
        nuevo = request.POST.get("estado_componente", "")
        validos = dict(ComponenteMaquina._meta.get_field("estado_componente").choices)
        if nuevo in validos:
            comp.estado_componente = nuevo
            comp.save(update_fields=["estado_componente"])
            registrar_auditoria(request, "componentes_maquina", comp.pk, "EDITAR",
                                f"Estado del componente -> {nuevo}")
            messages.info(request, f"Estado actualizado a {validos[nuevo]}.")
        else:
            messages.error(request, "Estado no válido.")
    return redirect("core:componente_detalle", pk=comp.pk)


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def componente_eliminar(request, pk):
    comp = get_object_or_404(ComponenteMaquina, pk=pk)
    id_maquina = comp.id_maquina_id
    if request.method == "POST":
        nombre = comp.nombre_componente
        registrar_auditoria(request, "componentes_maquina", comp.pk, "ELIMINAR",
                            f"Componente {nombre} eliminado")
        comp.delete()
        messages.success(request, f"Componente '{nombre}' eliminado.")
        return redirect("core:maquina_detalle", pk=id_maquina)
    return render(request, "core/componentes_eliminar.html", {"componente": comp})


# ------------------------- FALLAS PROBABLES -------------------------
def _guardar_falla(form, maquina=None):
    """Aplica el cálculo del nivel de riesgo y guarda la falla."""
    falla = form.save(commit=False)
    if maquina is not None:
        falla.id_maquina = maquina
    sugerido = sugerir_nivel_riesgo(
        falla.nivel_probabilidad, falla.severidad, falla.detectabilidad
    )
    falla.nivel_riesgo = combinar_riesgo(form.cleaned_data.get("nivel_riesgo"), sugerido)
    falla.save()
    return falla


@login_required
def falla_probable_list(request):
    qs = FallaProbable.objects.select_related("id_maquina", "id_componente")
    f_maquina = request.GET.get("maquina", "")
    f_riesgo = request.GET.get("riesgo", "")
    f_estado = request.GET.get("estado", "")
    buscar = request.GET.get("q", "").strip()
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    if f_riesgo:
        qs = qs.filter(nivel_riesgo=f_riesgo)
    if f_estado:
        qs = qs.filter(estado=f_estado)
    if buscar:
        qs = qs.filter(descripcion_falla__icontains=buscar)
    page = Paginator(qs.order_by("id_maquina"), PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "core/fallas_probables_list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(),
        "riesgos": FallaProbable._meta.get_field("nivel_riesgo").choices,
        "estados": FallaProbable._meta.get_field("estado").choices,
        "f_maquina": f_maquina, "f_riesgo": f_riesgo, "f_estado": f_estado, "q": buscar,
    })


@login_required
def falla_probable_detalle(request, pk):
    falla = get_object_or_404(
        FallaProbable.objects.select_related("id_maquina", "id_componente"), pk=pk
    )
    return render(request, "core/fallas_probables_detalle.html", {"falla": falla})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def falla_probable_crear(request, id_maquina=None):
    maquina = get_object_or_404(Maquina, pk=id_maquina) if id_maquina else None
    form = FallaProbableForm(request.POST or None, maquina=maquina)
    if request.method == "POST" and form.is_valid():
        falla = _guardar_falla(form, maquina)
        registrar_auditoria(request, "fallas_probables", falla.pk, "CREAR",
                            f"Falla probable ({falla.id_maquina.codigo_activo}) riesgo {falla.nivel_riesgo}")
        messages.success(request, f"Falla probable registrada. Nivel de riesgo: {falla.nivel_riesgo}.")
        if maquina is not None:
            return redirect("core:maquina_detalle", pk=maquina.pk)
        return redirect("core:falla_probable_detalle", pk=falla.pk)
    return render(request, "core/fallas_probables_form.html",
                  {"form": form, "titulo": "Nueva falla probable", "maquina": maquina})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def falla_probable_editar(request, pk):
    falla = get_object_or_404(FallaProbable, pk=pk)
    form = FallaProbableForm(request.POST or None, instance=falla)
    if request.method == "POST" and form.is_valid():
        falla = _guardar_falla(form)
        registrar_auditoria(request, "fallas_probables", falla.pk, "EDITAR",
                            f"Falla probable actualizada (riesgo {falla.nivel_riesgo})")
        messages.success(request, "Falla probable actualizada.")
        return redirect("core:falla_probable_detalle", pk=falla.pk)
    return render(request, "core/fallas_probables_form.html",
                  {"form": form, "titulo": "Editar falla probable", "maquina": falla.id_maquina})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def falla_probable_eliminar(request, pk):
    falla = get_object_or_404(FallaProbable, pk=pk)
    id_maquina = falla.id_maquina_id
    if request.method == "POST":
        registrar_auditoria(request, "fallas_probables", falla.pk, "ELIMINAR",
                            "Falla probable eliminada")
        falla.delete()
        messages.success(request, "Falla probable eliminada.")
        return redirect("core:maquina_detalle", pk=id_maquina)
    return render(request, "core/fallas_probables_eliminar.html", {"falla": falla})


# ------------------------- REPUESTOS CRÍTICOS POR MÁQUINA -------------------------
# Relación máquina-repuesto (tabla maquina_repuesto). Escritura: gestores.
from apps.core.services import repuestos_criticos_maquina  # noqa: E402


@login_required
def repuestos_criticos_list(request, id_maquina):
    maquina = get_object_or_404(Maquina, pk=id_maquina)
    items = repuestos_criticos_maquina(maquina)
    return render(request, "core/repuestos_criticos_maquina.html", {
        "maquina": maquina, "items": items,
        "hay_stock_bajo": any(getattr(i, "stock_bajo", False) for i in items),
    })


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def repuesto_critico_agregar(request, id_maquina):
    from apps.inventario.forms import MaquinaRepuestoForm
    from apps.inventario.models import MaquinaRepuesto

    maquina = get_object_or_404(Maquina, pk=id_maquina)
    form = MaquinaRepuestoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rel = form.save(commit=False)
        rel.id_maquina = maquina
        if MaquinaRepuesto.objects.filter(
            id_maquina=maquina, id_repuesto=rel.id_repuesto
        ).exists():
            messages.warning(request, "Ese repuesto ya está asociado a la máquina.")
            return redirect("core:repuestos_criticos_list", id_maquina=maquina.pk)
        rel.save()
        registrar_auditoria(request, "maquina_repuesto", rel.pk, "CREAR",
                            f"Repuesto crítico {rel.id_repuesto.codigo_repuesto} -> {maquina.codigo_activo}")
        messages.success(request, "Repuesto crítico asociado a la máquina.")
        return redirect("core:repuestos_criticos_list", id_maquina=maquina.pk)
    return render(request, "core/repuestos_critico_form.html",
                  {"form": form, "maquina": maquina, "titulo": "Asociar repuesto crítico"})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def repuesto_critico_editar(request, id_maquina, pk):
    from apps.inventario.forms import MaquinaRepuestoForm
    from apps.inventario.models import MaquinaRepuesto

    maquina = get_object_or_404(Maquina, pk=id_maquina)
    rel = get_object_or_404(MaquinaRepuesto, pk=pk, id_maquina=maquina)
    form = MaquinaRepuestoForm(request.POST or None, instance=rel)
    if request.method == "POST" and form.is_valid():
        rel = form.save()
        registrar_auditoria(request, "maquina_repuesto", rel.pk, "EDITAR",
                            f"Repuesto crítico {rel.id_repuesto.codigo_repuesto} ({maquina.codigo_activo})")
        messages.success(request, "Repuesto crítico actualizado.")
        return redirect("core:repuestos_criticos_list", id_maquina=maquina.pk)
    return render(request, "core/repuestos_critico_form.html",
                  {"form": form, "maquina": maquina, "titulo": "Editar repuesto crítico"})


@login_required
@rol_requerido(*GESTORES_ACTIVOS)
def repuesto_critico_eliminar(request, id_maquina, pk):
    from apps.inventario.models import MaquinaRepuesto

    maquina = get_object_or_404(Maquina, pk=id_maquina)
    rel = get_object_or_404(MaquinaRepuesto, pk=pk, id_maquina=maquina)
    if request.method == "POST":
        registrar_auditoria(request, "maquina_repuesto", rel.pk, "ELIMINAR",
                            f"Repuesto crítico desvinculado de {maquina.codigo_activo}")
        rel.delete()
        messages.success(request, "Repuesto crítico desvinculado de la máquina.")
        return redirect("core:repuestos_criticos_list", id_maquina=maquina.pk)
    return render(request, "core/repuestos_critico_eliminar.html",
                  {"rel": rel, "maquina": maquina})
