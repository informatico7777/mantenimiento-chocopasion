# Settings auxiliar para generar migraciones / checks sin MySQL.
from config.settings import *  # noqa
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
