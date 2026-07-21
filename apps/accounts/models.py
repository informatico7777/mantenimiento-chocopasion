"""
Modelos de seguridad mapeados a las tablas existentes `roles` y `usuarios`.

El modelo Usuario NO hereda de AbstractBaseUser porque la tabla `usuarios`
no posee la columna `last_login`. En su lugar implementa manualmente la
interfaz mínima que requieren el login de sesión y el middleware de auth.
"""
from django.contrib.auth.hashers import check_password, is_password_usable, make_password
from django.db import models
from django.utils.crypto import salted_hmac

from .managers import UsuarioManager
from config.base_model import MANAGED

# Choices reutilizables
ESTADO_ACTIVO = [("ACTIVO", "Activo"), ("INACTIVO", "Inactivo")]


class Rol(models.Model):
    """Catálogo de roles (ADMINISTRADOR, JEFE_PRODUCCION, ...)."""

    ADMINISTRADOR = "ADMINISTRADOR"
    JEFE_PRODUCCION = "JEFE_PRODUCCION"
    TECNICO_MANTENIMIENTO = "TECNICO_MANTENIMIENTO"
    OPERADOR = "OPERADOR"
    CONSULTA = "CONSULTA"

    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_ACTIVO, default="ACTIVO")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre_rol"]

    def __str__(self):
        return self.nombre_rol


class Usuario(models.Model):
    """Usuario del sistema mapeado a la tabla `usuarios`."""

    ESTADO_CHOICES = ESTADO_ACTIVO

    id_usuario = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, blank=True, null=True, unique=True)
    correo = models.EmailField(max_length=100, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    id_rol = models.ForeignKey(
        Rol, on_delete=models.DO_NOTHING, db_column="id_rol", related_name="usuarios"
    )
    id_area = models.ForeignKey(
        "core.Area",
        on_delete=models.DO_NOTHING,
        db_column="id_area",
        blank=True,
        null=True,
        related_name="usuarios",
    )
    usuario_login = models.CharField(max_length=50, unique=True)
    # La columna real es password_hash; Django usa el atributo `password`.
    password = models.CharField(max_length=255, db_column="password_hash")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="ACTIVO")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "usuario_login"
    REQUIRED_FIELDS = ["nombres", "apellidos"]

    class Meta:
        managed = MANAGED
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.nombre_completo} ({self.usuario_login})"

    # ----- Interfaz de autenticación -----
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return self.estado == "ACTIVO"

    @property
    def is_staff(self):
        return self.id_rol_id is not None and self.rol_nombre == Rol.ADMINISTRADOR

    @property
    def is_superuser(self):
        return self.rol_nombre == Rol.ADMINISTRADOR

    def get_username(self):
        return self.usuario_login

    def natural_key(self):
        return (self.usuario_login,)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        def setter(raw):
            self.set_password(raw)
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)

    def has_usable_password(self):
        return is_password_usable(self.password)

    def get_session_auth_hash(self):
        key_salt = "apps.accounts.models.Usuario.get_session_auth_hash"
        return salted_hmac(key_salt, self.password, algorithm="sha256").hexdigest()

    # Permisos: el control fino se hace por rol con decoradores propios.
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    # ----- Utilidades -----
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def rol_nombre(self):
        return self.id_rol.nombre_rol if self.id_rol_id else None

    def tiene_rol(self, *roles):
        return self.rol_nombre in roles
