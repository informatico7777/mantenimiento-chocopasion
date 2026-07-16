"""Backend de autenticación basado en la tabla `usuarios`."""
from django.contrib.auth.backends import BaseBackend

from .models import Usuario


class UsuarioLoginBackend(BaseBackend):
    """Autentica con `usuario_login` y verifica el hash de `password_hash`."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("usuario_login")
        if username is None or password is None:
            return None
        try:
            user = Usuario.objects.select_related("id_rol", "id_area").get(
                usuario_login=username
            )
        except Usuario.DoesNotExist:
            # Mitiga ataques de temporización ejecutando el hasher igualmente.
            Usuario().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user):
        return user.estado == "ACTIVO"

    def get_user(self, user_id):
        try:
            return Usuario.objects.select_related("id_rol", "id_area").get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
