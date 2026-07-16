from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Autenticación y usuarios"

    def ready(self):
        # La tabla `usuarios` no tiene columna last_login, por lo que se
        # desconecta la señal que intenta actualizarla en cada login.
        from django.contrib.auth import user_logged_in
        from django.contrib.auth.models import update_last_login

        user_logged_in.disconnect(update_last_login)
