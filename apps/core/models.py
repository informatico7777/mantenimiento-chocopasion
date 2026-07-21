"""Modelos del núcleo: áreas, máquinas, funciones, componentes, fallas e historial."""
from django.db import models

from .choices import (
    CRITICIDAD,
    ESTADO_AREA,
    ESTADO_GENERICO,
    ESTADO_OPERATIVO,
    NIVEL_RIESGO,
    TIPO_ENERGIA_MAQUINA,
)
from config.base_model import MANAGED


class Area(models.Model):
    id_area = models.AutoField(primary_key=True)
    nombre_area = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    responsable_area = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.DO_NOTHING,
        db_column="responsable_area",
        blank=True,
        null=True,
        related_name="areas_responsable",
    )
    estado = models.CharField(max_length=10, choices=ESTADO_AREA, default="ACTIVA")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "areas"
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ["nombre_area"]

    def __str__(self):
        return self.nombre_area


class Maquina(models.Model):
    id_maquina = models.AutoField(primary_key=True)
    codigo_activo = models.CharField(max_length=30, unique=True)
    nombre_maquina = models.CharField(max_length=150)
    tipo_maquina = models.CharField(max_length=100)
    id_area = models.ForeignKey(
        Area, on_delete=models.DO_NOTHING, db_column="id_area", related_name="maquinas"
    )
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    capacidad_valor = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    capacidad_unidad = models.CharField(max_length=30, blank=True, null=True)
    tipo_energia = models.CharField(
        max_length=20, choices=TIPO_ENERGIA_MAQUINA, default="ELECTRICA"
    )
    potencia_kw = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    potencia_hp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    consumo_estimado_hora = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    consumo_estimado_lote = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    criticidad = models.CharField(max_length=10, choices=CRITICIDAD, default="MEDIA")
    estado_operativo = models.CharField(
        max_length=30, choices=ESTADO_OPERATIVO, default="OPERATIVA"
    )
    ubicacion_fisica = models.CharField(max_length=150, blank=True, null=True)
    fecha_instalacion = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    responsable_maquina = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.DO_NOTHING,
        db_column="responsable_maquina",
        blank=True,
        null=True,
        related_name="maquinas_responsable",
    )
    requiere_checklist_diario = models.BooleanField(default=True)
    requiere_calibracion = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "maquinas"
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"
        ordering = ["codigo_activo"]

    def __str__(self):
        return f"{self.codigo_activo} - {self.nombre_maquina}"

    @property
    def badge_estado(self):
        """Clase Bootstrap según el estado operativo."""
        return {
            "OPERATIVA": "success",
            "OBSERVADA": "warning",
            "PARADA": "secondary",
            "MANTENIMIENTO_PREVENTIVO": "info",
            "MANTENIMIENTO_CORRECTIVO": "primary",
            "FUERA_DE_SERVICIO": "danger",
        }.get(self.estado_operativo, "secondary")


class FuncionProceso(models.Model):
    id_funcion = models.AutoField(primary_key=True)
    numero_etapa = models.IntegerField()
    nombre_etapa = models.CharField(max_length=100)
    funcion_principal = models.TextField()
    criticidad_funcion = models.CharField(max_length=10, choices=CRITICIDAD, default="MEDIA")
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_GENERICO, default="ACTIVA")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "funciones_proceso"
        verbose_name = "Función de proceso"
        verbose_name_plural = "Funciones de proceso"
        ordering = ["numero_etapa"]

    def __str__(self):
        return f"{self.numero_etapa}. {self.nombre_etapa}"


class MaquinaFuncion(models.Model):
    id_maquina_funcion = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        Maquina, on_delete=models.DO_NOTHING, db_column="id_maquina", related_name="funciones"
    )
    id_funcion = models.ForeignKey(
        FuncionProceso, on_delete=models.DO_NOTHING, db_column="id_funcion",
        related_name="maquinas",
    )
    es_funcion_principal = models.BooleanField(default=False)
    observacion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED
        db_table = "maquina_funcion"
        verbose_name = "Máquina-Función"
        verbose_name_plural = "Máquinas-Funciones"

    def __str__(self):
        return f"{self.id_maquina_id} - {self.id_funcion_id}"


class ComponenteMaquina(models.Model):
    TIPO_COMPONENTE = [
        ("MECANICO", "Mecánico"),
        ("ELECTRICO", "Eléctrico"),
        ("ELECTRONICO", "Electrónico"),
        ("TERMICO", "Térmico"),
        ("NEUMATICO", "Neumático"),
        ("REFRIGERACION", "Refrigeración"),
        ("SANITARIO", "Sanitario"),
        ("OTRO", "Otro"),
    ]
    ESTADO_COMPONENTE = [
        ("BUENO", "Bueno"),
        ("OBSERVADO", "Observado"),
        ("DANADO", "Dañado"),
        ("CAMBIADO", "Cambiado"),
        ("FUERA_DE_SERVICIO", "Fuera de servicio"),
    ]

    id_componente = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        Maquina, on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="componentes",
    )
    nombre_componente = models.CharField(max_length=100)
    tipo_componente = models.CharField(max_length=20, choices=TIPO_COMPONENTE, default="OTRO")
    descripcion = models.TextField(blank=True, null=True)
    vida_util_estimada_horas = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    criticidad_componente = models.CharField(max_length=10, choices=CRITICIDAD, default="MEDIA")
    requiere_lubricacion = models.BooleanField(default=False)
    requiere_calibracion = models.BooleanField(default=False)
    estado_componente = models.CharField(
        max_length=20, choices=ESTADO_COMPONENTE, default="BUENO"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "componentes_maquina"
        verbose_name = "Componente"
        verbose_name_plural = "Componentes"
        ordering = ["nombre_componente"]

    def __str__(self):
        return self.nombre_componente


class FallaProbable(models.Model):
    id_falla_probable = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        Maquina, on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="fallas_probables",
    )
    id_componente = models.ForeignKey(
        ComponenteMaquina, on_delete=models.DO_NOTHING, db_column="id_componente",
        blank=True, null=True, related_name="fallas_probables",
    )
    descripcion_falla = models.TextField()
    causa_probable = models.TextField(blank=True, null=True)
    efecto_en_produccion = models.TextField(blank=True, null=True)
    probabilidad_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    nivel_probabilidad = models.CharField(max_length=10, choices=CRITICIDAD, default="MEDIA")
    severidad = models.IntegerField(blank=True, null=True)
    detectabilidad = models.IntegerField(blank=True, null=True)
    nivel_riesgo = models.CharField(max_length=10, choices=NIVEL_RIESGO, default="MEDIO")
    accion_preventiva_sugerida = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_GENERICO, default="ACTIVA")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "fallas_probables"
        verbose_name = "Falla probable"
        verbose_name_plural = "Fallas probables"

    def __str__(self):
        return self.descripcion_falla[:60]


class HistorialEstadoMaquina(models.Model):
    id_historial = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        Maquina, on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="historial_estados",
    )
    estado_anterior = models.CharField(
        max_length=30, choices=ESTADO_OPERATIVO, blank=True, null=True
    )
    estado_nuevo = models.CharField(max_length=30, choices=ESTADO_OPERATIVO)
    motivo_cambio = models.TextField(blank=True, null=True)
    fecha_hora_cambio = models.DateTimeField(auto_now_add=True)
    id_usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="id_usuario",
        related_name="cambios_estado_maquina",
    )
    id_ot = models.ForeignKey(
        "mantenimiento.OrdenTrabajo", on_delete=models.DO_NOTHING, db_column="id_ot",
        blank=True, null=True, related_name="historial_estados",
    )
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = MANAGED
        db_table = "historial_estado_maquina"
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historial de estados"
        ordering = ["-fecha_hora_cambio"]

    def __str__(self):
        return f"{self.id_maquina_id}: {self.estado_anterior} -> {self.estado_nuevo}"
