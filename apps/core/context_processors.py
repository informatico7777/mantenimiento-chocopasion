"""Context processor que expone datos comunes a todas las plantillas."""


def menu_context(request):
    user = getattr(request, "user", None)
    rol = getattr(user, "rol_nombre", None) if user and user.is_authenticated else None
    return {
        "APP_NOMBRE": "Mantenimiento Choco Pasión",
        "APP_PLANTA": "Choco Pasión - Tingo María",
        "ROL_ACTUAL": rol,
        "ES_ADMINISTRADOR": rol == "ADMINISTRADOR",
        "PUEDE_GESTIONAR_ACTIVOS": rol in (
            "ADMINISTRADOR", "JEFE_PRODUCCION", "TECNICO_MANTENIMIENTO"
        ),
    }
