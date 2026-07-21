"""
Configuración dinámica para modelos administrados por Django.

- MySQL local: managed=False.
- Heroku/PostgreSQL: managed=True mediante DATABASE_URL.
- Generación local de migraciones: FORCE_MANAGED_MODELS=True.
"""
import os


def env_is_true(variable_name: str) -> bool:
    value = os.environ.get(variable_name, "")
    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "si",
        "sí",
    }


def is_heroku() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


MANAGED = is_heroku() or env_is_true("FORCE_MANAGED_MODELS")