"""Helper para registrar acciones en la tabla `auditoria_sistema`."""
import logging

logger = logging.getLogger("apps")


def _client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def registrar_auditoria(request, tabla_afectada, id_registro, accion, descripcion=""):
    """
    Registra una acción en auditoria_sistema. Nunca interrumpe el flujo
    principal: si falla el registro, solo se loguea el error.

    accion: CREAR, EDITAR, ELIMINAR, DESCARGAR, GENERAR_REPORTE, LOGIN, LOGOUT, OTRO
    """
    from apps.reportes.models import AuditoriaSistema

    try:
        usuario = None
        if request is not None and getattr(request, "user", None) is not None:
            if request.user.is_authenticated:
                usuario_id = request.user.pk
            else:
                usuario_id = None
        else:
            usuario_id = None

        AuditoriaSistema.objects.create(
            id_usuario_id=usuario_id,
            tabla_afectada=tabla_afectada,
            id_registro_afectado=id_registro,
            accion=accion,
            descripcion=descripcion,
            ip_origen=_client_ip(request),
        )
    except Exception as exc:  # pragma: no cover - la auditoría no debe romper la app
        logger.error("No se pudo registrar auditoría: %s", exc)
