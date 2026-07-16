"""
Establece o reinicia la contraseña de un usuario de la tabla `usuarios`,
guardándola con el hasher seguro de Django (PBKDF2).

Uso:
    python manage.py set_password admin --password "MiClaveSegura123"
    python manage.py set_password admin            (la pedirá de forma interactiva)
"""
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Usuario


class Command(BaseCommand):
    help = "Establece la contraseña (hash seguro) de un usuario existente."

    def add_arguments(self, parser):
        parser.add_argument("usuario_login", type=str, help="usuario_login del usuario")
        parser.add_argument("--password", type=str, default=None,
                            help="Nueva contraseña (si se omite, se pide por consola).")

    def handle(self, *args, **options):
        login = options["usuario_login"]
        try:
            user = Usuario.objects.get(usuario_login=login)
        except Usuario.DoesNotExist:
            raise CommandError(f"No existe el usuario '{login}'.")

        password = options["password"]
        if not password:
            password = getpass("Nueva contraseña: ")
            confirmar = getpass("Confirmar contraseña: ")
            if password != confirmar:
                raise CommandError("Las contraseñas no coinciden.")
        if len(password) < 6:
            raise CommandError("La contraseña debe tener al menos 6 caracteres.")

        user.set_password(password)
        user.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS(
            f"Contraseña actualizada para '{login}'."
        ))
