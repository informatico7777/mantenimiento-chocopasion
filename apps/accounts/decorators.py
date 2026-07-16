"""Decoradores para restringir vistas por rol."""
from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def rol_requerido(*roles_permitidos):
    """
    Permite el acceso solo a usuarios cuyo rol esté en `roles_permitidos`.
    ADMINISTRADOR siempre tiene acceso.

    Uso:
        @login_required
        @rol_requerido('JEFE_PRODUCCION', 'TECNICO_MANTENIMIENTO')
        def mi_vista(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect("accounts:login")
            rol = getattr(user, "rol_nombre", None)
            if rol == "ADMINISTRADOR" or rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tiene permisos para acceder a esta sección.")
            raise PermissionDenied("Rol no autorizado.")

        return _wrapped

    return decorator
