from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password


class UsuarioManager(BaseUserManager):
    """Manager para el modelo Usuario mapeado a la tabla `usuarios`."""

    use_in_migrations = False

    def get_by_natural_key(self, username):
        return self.get(usuario_login=username)

    def create_user(self, usuario_login, nombres, apellidos, id_rol, password=None, **extra):
        if not usuario_login:
            raise ValueError("El usuario_login es obligatorio.")
        user = self.model(
            usuario_login=usuario_login,
            nombres=nombres,
            apellidos=apellidos,
            id_rol=id_rol,
            **extra,
        )
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, usuario_login, nombres, apellidos, id_rol, password=None, **extra):
        extra.setdefault("estado", "ACTIVO")
        return self.create_user(usuario_login, nombres, apellidos, id_rol, password, **extra)
