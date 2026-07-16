"""Choices compartidos que reflejan los ENUM de MySQL."""

CRITICIDAD = [
    ("BAJA", "Baja"),
    ("MEDIA", "Media"),
    ("ALTA", "Alta"),
    ("MUY_ALTA", "Muy alta"),
]

NIVEL_ALERTA = [
    ("BAJO", "Bajo"),
    ("MEDIO", "Medio"),
    ("ALTO", "Alto"),
    ("CRITICO", "Crítico"),
]

NIVEL_RIESGO = [
    ("BAJO", "Bajo"),
    ("MEDIO", "Medio"),
    ("ALTO", "Alto"),
    ("CRITICO", "Crítico"),
]

ESTADO_OPERATIVO = [
    ("OPERATIVA", "Operativa"),
    ("OBSERVADA", "Observada"),
    ("PARADA", "Parada"),
    ("MANTENIMIENTO_PREVENTIVO", "Mantenimiento preventivo"),
    ("MANTENIMIENTO_CORRECTIVO", "Mantenimiento correctivo"),
    ("FUERA_DE_SERVICIO", "Fuera de servicio"),
]

TIPO_ENERGIA_MAQUINA = [
    ("ELECTRICA", "Eléctrica"),
    ("GLP", "GLP"),
    ("NEUMATICA", "Neumática"),
    ("MIXTA", "Mixta"),
    ("BATERIA", "Batería"),
    ("NO_APLICA", "No aplica"),
]

ESTADO_AREA = [("ACTIVA", "Activa"), ("INACTIVA", "Inactiva")]
ESTADO_GENERICO = [("ACTIVA", "Activa"), ("INACTIVA", "Inactiva")]

TURNO = [
    ("MANANA", "Mañana"),
    ("TARDE", "Tarde"),
    ("NOCHE", "Noche"),
    ("UNICO", "Único"),
]
