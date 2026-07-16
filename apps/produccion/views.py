"""Vistas de producción y energía."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from apps.accounts.decorators import rol_requerido
from apps.core.audit import registrar_auditoria
from apps.core.models import Maquina

from .forms import ConsumoEnergeticoForm, LoteProduccionForm
from .models import ConsumoEnergetico, LoteProduccion

PAGINATE_BY = 15


@login_required
def lote_list(request):
    qs = LoteProduccion.objects.select_related("responsable_produccion")
    f_estado = request.GET.get("estado", "")
    if f_estado:
        qs = qs.filter(estado_lote=f_estado)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "produccion/lotes_list.html", {
        "page_obj": page, "estados": LoteProduccion._meta.get_field("estado_lote").choices,
        "f_estado": f_estado,
    })


@login_required
@rol_requerido("JEFE_PRODUCCION", "OPERADOR")
def lote_crear(request):
    form = LoteProduccionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        lote = form.save()
        registrar_auditoria(request, "lotes_produccion", lote.pk, "CREAR", lote.codigo_lote)
        messages.success(request, "Lote de producción registrado.")
        return redirect("produccion:lote_list")
    return render(request, "produccion/lote_form.html",
                  {"form": form, "titulo": "Nuevo lote de producción"})


@login_required
def consumo_list(request):
    qs = ConsumoEnergetico.objects.select_related("id_maquina", "id_lote")
    f_maquina = request.GET.get("maquina", "")
    if f_maquina:
        qs = qs.filter(id_maquina_id=f_maquina)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "produccion/energia_list.html", {
        "page_obj": page, "maquinas": Maquina.objects.all(), "f_maquina": f_maquina,
    })


@login_required
@rol_requerido("JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO", "OPERADOR")
def consumo_crear(request):
    form = ConsumoEnergeticoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        consumo = form.save()
        registrar_auditoria(request, "consumo_energetico", consumo.pk, "CREAR",
                            f"Consumo {consumo.id_maquina_id} {consumo.fecha}")
        messages.success(request, "Consumo energético registrado.")
        return redirect("produccion:consumo_list")
    return render(request, "produccion/energia_form.html",
                  {"form": form, "titulo": "Registrar consumo energético"})
