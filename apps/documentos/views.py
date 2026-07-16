"""Vistas de archivos adjuntos: listado, subida y descarga."""
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.core.audit import registrar_auditoria

from .forms import ArchivoAdjuntoForm
from .models import ArchivoAdjunto

PAGINATE_BY = 20


@login_required
def documento_list(request):
    qs = ArchivoAdjunto.objects.filter(estado="ACTIVO").select_related("subido_por")
    f_tipo = request.GET.get("tipo_entidad", "")
    f_categoria = request.GET.get("categoria", "")
    if f_tipo:
        qs = qs.filter(tipo_entidad=f_tipo)
    if f_categoria:
        qs = qs.filter(categoria_archivo=f_categoria)
    page = Paginator(qs, PAGINATE_BY).get_page(request.GET.get("page"))
    return render(request, "documentos/list.html", {
        "page_obj": page,
        "tipos_entidad": ArchivoAdjunto.TIPO_ENTIDAD,
        "categorias": ArchivoAdjunto.CATEGORIA,
        "f_tipo": f_tipo, "f_categoria": f_categoria,
    })


@login_required
def documento_subir(request):
    inicial = {}
    if request.method == "GET":
        # Permite precargar entidad desde un detalle (?tipo=MAQUINA&id=3&categoria=FOTO_MAQUINA)
        if request.GET.get("tipo"):
            inicial["tipo_entidad"] = request.GET["tipo"]
        if request.GET.get("id"):
            inicial["id_entidad"] = request.GET["id"]
        if request.GET.get("categoria"):
            inicial["categoria_archivo"] = request.GET["categoria"]

    form = ArchivoAdjuntoForm(request.POST or None, request.FILES or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        archivo = form.cleaned_data["archivo"]
        categoria = form.cleaned_data["categoria_archivo"]
        subdir = settings.MEDIA_SUBDIRS.get(categoria, "maquinas")

        # Nombre seguro con marca de tiempo para evitar colisiones.
        base = os.path.basename(archivo.name)
        ext = base.rsplit(".", 1)[-1].upper() if "." in base else "OTRO"
        ts = timezone.now().strftime("%Y%m%d%H%M%S")
        nombre_guardado = f"{ts}_{base}"

        fs = FileSystemStorage(
            location=os.path.join(settings.MEDIA_ROOT, subdir),
            base_url=f"{settings.MEDIA_URL}{subdir}/",
        )
        guardado = fs.save(nombre_guardado, archivo)
        ruta_relativa = f"{subdir}/{guardado}"

        tipo_archivo = ext if ext in dict(ArchivoAdjunto.TIPO_ARCHIVO) else "OTRO"
        adj = ArchivoAdjunto.objects.create(
            tipo_entidad=form.cleaned_data["tipo_entidad"],
            id_entidad=form.cleaned_data["id_entidad"],
            categoria_archivo=categoria,
            nombre_archivo=base,
            tipo_archivo=tipo_archivo,
            ruta_archivo=ruta_relativa,
            descargable=True,
            subido_por_id=request.user.pk,
            descripcion=form.cleaned_data.get("descripcion") or None,
            estado="ACTIVO",
        )
        registrar_auditoria(request, "archivos_adjuntos", adj.pk, "CREAR",
                            f"Subida de {base} ({categoria})")
        messages.success(request, "Archivo subido y registrado correctamente.")
        return redirect("documentos:documento_list")

    return render(request, "documentos/form.html", {"form": form, "titulo": "Subir archivo"})


@login_required
def documento_descargar(request, pk):
    adj = get_object_or_404(ArchivoAdjunto, pk=pk, estado="ACTIVO")
    ruta_absoluta = os.path.join(settings.MEDIA_ROOT, adj.ruta_archivo)
    if not os.path.exists(ruta_absoluta):
        raise Http404("El archivo no existe en el servidor.")
    registrar_auditoria(request, "archivos_adjuntos", adj.pk, "DESCARGAR",
                        f"Descarga de {adj.nombre_archivo}")
    return FileResponse(
        open(ruta_absoluta, "rb"), as_attachment=True, filename=adj.nombre_archivo
    )
