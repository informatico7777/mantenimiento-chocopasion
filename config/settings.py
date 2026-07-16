"""
Configuración de Django para el proyecto mantenimiento_chocopasion.
Sistema de Gestión de Mantenimiento - Choco Pasión (Tingo María).

Las credenciales se leen desde un archivo .env mediante python-decouple.
NO se debe quemar la contraseña directamente en este archivo.
"""
from pathlib import Path

from decouple import Csv, config

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="clave-insegura-solo-desarrollo")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Apps del proyecto
    "apps.accounts",
    "apps.core",
    "apps.mantenimiento",
    "apps.inventario",
    "apps.produccion",
    "apps.documentos",
    "apps.reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.menu_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Base de datos (MySQL 8.4 / InnoDB). Credenciales desde .env
# ---------------------------------------------------------------------------
_DB_ENGINE = config("DB_ENGINE", default="django.db.backends.mysql")
DATABASES = {
    "default": {
        "ENGINE": _DB_ENGINE,
        "NAME": config("DB_NAME", default="bd_mantenimiento_chocopasion"),
        "USER": config("DB_USER", default="root"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="3306"),
    }
}
# Opciones específicas de MySQL (charset utf8mb4 y modo estricto).
if "mysql" in _DB_ENGINE:
    DATABASES["default"]["OPTIONS"] = {
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }

# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.Usuario"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.UsuarioLoginBackend",
]

# Hashers: PBKDF2 (Django) por defecto y bcrypt para hashes heredados ($2y$/$2b$).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = False  # La BD trabaja en hora local (-05:00).

# ---------------------------------------------------------------------------
# Archivos estáticos y multimedia
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Subcarpetas de media por categoría de archivo.
MEDIA_SUBDIRS = {
    "FOTO_MAQUINA": "maquinas",
    "PLACA_TECNICA": "placas",
    "FICHA_TECNICA": "fichas_tecnicas",
    "MANUAL": "manuales",
    "EVIDENCIA": "evidencias",
    "PDF": "reportes_pdf",
    "INFORME": "reportes_pdf",
    "OTRO": "maquinas",
}

# Límite de subida (10 MB) y extensiones permitidas.
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_UPLOAD_EXTENSIONS = ["jpg", "jpeg", "png", "pdf", "docx", "xlsx", "csv", "txt"]

# ---------------------------------------------------------------------------
# Otros
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Paginación por defecto en listados.
PAGINATE_BY = 15

# Mensajes -> clases de Bootstrap 5.
from django.contrib.messages import constants as messages  # noqa: E402

MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# Logging básico para errores de base de datos y aplicación.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.db.backends": {"handlers": ["console"], "level": "ERROR"},
        "apps": {"handlers": ["console"], "level": "INFO"},
    },
}
