"""
Módulo de consulta de la auditoría del sistema.

La ESCRITURA de auditoría vive en apps/core/audit.py (helper
`registrar_auditoria`), que ya se usa en todo el proyecto y nunca bloquea la
operación principal. Este módulo se encarga de la LECTURA: construir el
queryset filtrado, exponer las opciones de filtro y preparar los datos para la
pantalla y las exportaciones.

No modifica la base de datos ni su estructura. Solo consulta la tabla existente
`auditoria_sistema` (modelo AuditoriaSistema, managed=False).
"""

# Acciones consideradas (coinciden con el ENUM de la tabla).
ACCIONES = [
    ("CREAR", "Crear"),
    ("EDITAR", "Editar"),
    ("ELIMINAR", "Eliminar"),
    ("DESCARGAR", "Descargar"),
    ("GENERAR_REPORTE", "Generar reporte"),
    ("LOGIN", "Login"),
    ("LOGOUT", "Logout"),
    ("OTRO", "Otro"),
]

# Clases de color (Bootstrap) por acción, para las badges.
BADGE_ACCION = {
    "CREAR": "success",
    "EDITAR": "info",
    "ELIMINAR": "danger",
    "DESCARGAR": "secondary",
    "GENERAR_REPORTE": "primary",
    "LOGIN": "success",
    "LOGOUT": "dark",
    "OTRO": "secondary",
}


def badge_accion(accion):
    return BADGE_ACCION.get(accion, "secondary")


def tablas_disponibles():
    """Lista de tablas afectadas presentes en la auditoría (para el filtro)."""
    from apps.reportes.models import AuditoriaSistema

    return list(
        AuditoriaSistema.objects.order_by("tabla_afectada")
        .values_list("tabla_afectada", flat=True)
        .distinct()
    )


def filtrar_auditoria(filtros):
    """
    Construye el queryset de auditoría aplicando los filtros recibidos.

    `filtros` es un dict (típicamente form.cleaned_data) con las claves:
      usuario, accion, tabla, fecha_inicio, fecha_fin, q (descripción).

    Devuelve un queryset ordenado del más reciente al más antiguo.
    """
    from apps.reportes.models import AuditoriaSistema

    qs = AuditoriaSistema.objects.select_related("id_usuario").all()

    usuario = filtros.get("usuario")
    accion = filtros.get("accion")
    tabla = filtros.get("tabla")
    fecha_inicio = filtros.get("fecha_inicio")
    fecha_fin = filtros.get("fecha_fin")
    q = filtros.get("q")

    if usuario:
        qs = qs.filter(id_usuario=usuario)
    if accion:
        qs = qs.filter(accion=accion)
    if tabla:
        qs = qs.filter(tabla_afectada=tabla)
    if fecha_inicio:
        qs = qs.filter(fecha_hora__date__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(fecha_hora__date__lte=fecha_fin)
    if q:
        qs = qs.filter(descripcion__icontains=q)

    return qs.order_by("-fecha_hora")
