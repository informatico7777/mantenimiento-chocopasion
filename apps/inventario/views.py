"""Vistas de inventario: repuestos, proveedores y servicios externos."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import rol_requerido
from apps.core.audit import registrar_auditoria

from .forms import (
    MovimientoRepuestoForm,
    ProveedorForm,
    RepuestoForm,
    ServicioExternoForm,
)
from .models import MovimientoRepuesto, Proveedor, Repuesto, ServicioExterno

PAGINATE_BY = 15


# ----------------------------- REPUESTOS -----------------------------
@login_required
def repuesto_list(request):
    qs = Repuesto.objects.select_related("id_proveedor")
    buscar = request.GET.get("q", "").strip()
    solo_bajo = request.GET.get("bajo_stock", "")
    if buscar:
        qs = qs.filter(
            Q(nombre_repuesto__icontains=buscar) | Q(codigo_repuesto__icontains=buscar)
        )
    if solo_bajo == "1":
        qs = qs.filter(stock_actual__lte=F("stock_minimo"))
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "repuestos/list.html",
                  {"page_obj": page, "q": buscar, "solo_bajo": solo_bajo})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def repuesto_crear(request):
    form = RepuestoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        rep = form.save()
        registrar_auditoria(request, "repuestos", rep.pk, "CREAR", rep.codigo_repuesto)
        messages.success(request, "Repuesto registrado.")
        return redirect("inventario:repuesto_list")
    return render(request, "repuestos/form.html",
                  {"form": form, "titulo": "Nuevo repuesto"})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def repuesto_editar(request, pk):
    rep = get_object_or_404(Repuesto, pk=pk)
    form = RepuestoForm(request.POST or None, instance=rep)
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar_auditoria(request, "repuestos", rep.pk, "EDITAR", rep.codigo_repuesto)
        messages.success(request, "Repuesto actualizado.")
        return redirect("inventario:repuesto_list")
    return render(request, "repuestos/form.html",
                  {"form": form, "titulo": f"Editar {rep.codigo_repuesto}"})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def repuesto_movimiento(request, pk):
    """Registra un movimiento. El stock se actualiza por trigger en la BD."""
    rep = get_object_or_404(Repuesto, pk=pk)
    form = MovimientoRepuestoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        mov = form.save(commit=False)
        mov.id_repuesto = rep
        mov.responsable_id = request.user.pk
        mov.save()
        registrar_auditoria(request, "movimiento_repuestos", mov.pk, "CREAR",
                            f"{mov.tipo_movimiento} {mov.cantidad} de {rep.codigo_repuesto}")
        messages.success(request, "Movimiento registrado. El stock se actualizó automáticamente.")
        return redirect("inventario:repuesto_list")
    movimientos = rep.movimientos.select_related("responsable")[:20]
    return render(request, "repuestos/movimiento_form.html",
                  {"form": form, "repuesto": rep, "movimientos": movimientos})


# ----------------------------- PROVEEDORES -----------------------------
@login_required
def proveedor_list(request):
    qs = Proveedor.objects.all()
    f_tipo = request.GET.get("tipo", "")
    if f_tipo:
        qs = qs.filter(tipo_proveedor=f_tipo)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "repuestos/proveedores_list.html", {
        "page_obj": page, "tipos": Proveedor._meta.get_field("tipo_proveedor").choices,
        "f_tipo": f_tipo,
    })


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def proveedor_crear(request):
    form = ProveedorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        prov = form.save()
        registrar_auditoria(request, "proveedores", prov.pk, "CREAR", prov.nombre_proveedor)
        messages.success(request, "Proveedor registrado.")
        return redirect("inventario:proveedor_list")
    return render(request, "repuestos/proveedor_form.html",
                  {"form": form, "titulo": "Nuevo proveedor"})


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def proveedor_editar(request, pk):
    prov = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=prov)
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar_auditoria(request, "proveedores", prov.pk, "EDITAR", prov.nombre_proveedor)
        messages.success(request, "Proveedor actualizado.")
        return redirect("inventario:proveedor_list")
    return render(request, "repuestos/proveedor_form.html",
                  {"form": form, "titulo": "Editar proveedor"})


# ----------------------------- SERVICIOS EXTERNOS -----------------------------
@login_required
def servicio_list(request):
    qs = ServicioExterno.objects.select_related("id_maquina", "id_proveedor", "id_ot")
    f_estado = request.GET.get("estado", "")
    if f_estado:
        qs = qs.filter(estado_servicio=f_estado)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "repuestos/servicios_list.html", {
        "page_obj": page, "estados": ServicioExterno._meta.get_field("estado_servicio").choices,
        "f_estado": f_estado,
    })


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO")
def servicio_crear(request):
    form = ServicioExternoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        serv = form.save()
        registrar_auditoria(request, "servicios_externos", serv.pk, "CREAR",
                            f"Servicio externo OT {serv.id_ot_id}")
        messages.success(request, "Servicio externo registrado.")
        return redirect("inventario:servicio_list")
    return render(request, "repuestos/servicio_form.html",
                  {"form": form, "titulo": "Nuevo servicio externo"})
