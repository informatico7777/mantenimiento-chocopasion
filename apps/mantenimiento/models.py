"""Modelos de mantenimiento: checklist, observaciones, fallas, planes y órdenes."""
from django.db import models

from apps.core.choices import NIVEL_ALERTA, TURNO


class ChecklistPlantilla(models.Model):
    TIPO_RESPUESTA = [
        ("SI_NO", "Sí / No"),
        ("TEXTO", "Texto"),
        ("NUMERO", "Número"),
        ("TEMPERATURA", "Temperatura"),
        ("OBSERVACION", "Observación"),
    ]
    FRECUENCIA = [
        ("DIARIO", "Diario"),
        ("SEMANAL", "Semanal"),
        ("MENSUAL", "Mensual"),
        ("POR_LOTE", "Por lote"),
    ]
    ESTADO = [("ACTIVO", "Activo"), ("INACTIVO", "Inactivo")]

    id_item_checklist = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="items_checklist",
    )
    pregunta = models.TextField()
    tipo_respuesta = models.CharField(max_length=15, choices=TIPO_RESPUESTA, default="SI_NO")
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    valor_maximo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unidad_medida = models.CharField(max_length=30, blank=True, null=True)
    obligatorio = models.BooleanField(default=True)
    bloquea_produccion = models.BooleanField(default=False)
    frecuencia = models.CharField(max_length=10, choices=FRECUENCIA, default="DIARIO")
    estado = models.CharField(max_length=10, choices=ESTADO, default="ACTIVO")
    orden_visualizacion = models.IntegerField(default=1)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "checklist_plantilla"
        verbose_name = "Ítem de checklist"
        verbose_name_plural = "Plantilla de checklist"
        ordering = ["id_maquina", "orden_visualizacion"]

    def __str__(self):
        return self.pregunta[:60]


class ChecklistEjecucion(models.Model):
    RESULTADO = [
        ("APTA", "Apta"),
        ("OBSERVADA", "Observada"),
        ("NO_APTA", "No apta"),
    ]

    id_checklist = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="checklists",
    )
    id_usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="id_usuario",
        related_name="checklists",
    )
    fecha = models.DateField()
    turno = models.CharField(max_length=10, choices=TURNO, default="MANANA")
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    resultado_general = models.CharField(max_length=10, choices=RESULTADO, default="APTA")
    permite_produccion = models.BooleanField(default=True)
    observacion_general = models.TextField(blank=True, null=True)
    firma_responsable = models.CharField(max_length=150, blank=True, null=True)
    genero_reporte_falla = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "checklist_ejecucion"
        verbose_name = "Ejecución de checklist"
        verbose_name_plural = "Ejecuciones de checklist"
        ordering = ["-fecha", "-creado_en"]

    def __str__(self):
        return f"Checklist {self.id_maquina_id} {self.fecha} ({self.resultado_general})"

    @property
    def badge_resultado(self):
        return {"APTA": "success", "OBSERVADA": "warning", "NO_APTA": "danger"}.get(
            self.resultado_general, "secondary"
        )


class ChecklistDetalle(models.Model):
    id_checklist_detalle = models.AutoField(primary_key=True)
    id_checklist = models.ForeignKey(
        ChecklistEjecucion, on_delete=models.DO_NOTHING, db_column="id_checklist",
        related_name="detalles",
    )
    id_item_checklist = models.ForeignKey(
        ChecklistPlantilla, on_delete=models.DO_NOTHING, db_column="id_item_checklist",
        related_name="detalles",
    )
    respuesta = models.TextField(blank=True, null=True)
    valor_medido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cumple = models.BooleanField(default=True)
    observacion = models.TextField(blank=True, null=True)
    requiere_ot = models.BooleanField(default=False)
    nivel_alerta = models.CharField(max_length=10, choices=NIVEL_ALERTA, default="BAJO")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "checklist_detalle"
        verbose_name = "Detalle de checklist"
        verbose_name_plural = "Detalles de checklist"

    def __str__(self):
        return f"Detalle {self.id_checklist_id} - item {self.id_item_checklist_id}"


class ObservacionDiaria(models.Model):
    TIPO_OBSERVACION = [
        ("RUIDO", "Ruido"), ("VIBRACION", "Vibración"), ("TEMPERATURA", "Temperatura"),
        ("FUGA", "Fuga"), ("LIMPIEZA", "Limpieza"), ("ENERGIA", "Energía"),
        ("FALLA", "Falla"), ("CALIDAD", "Calidad"), ("SEGURIDAD", "Seguridad"),
        ("OTRO", "Otro"),
    ]
    ESTADO_OBSERVACION = [
        ("PENDIENTE", "Pendiente"),
        ("REVISADA", "Revisada"),
        ("CONVERTIDA_A_OT", "Convertida a OT"),
        ("CERRADA", "Cerrada"),
    ]

    id_observacion = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="observaciones_diarias",
    )
    id_usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="id_usuario",
        related_name="observaciones_diarias",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    turno = models.CharField(max_length=10, choices=TURNO, default="MANANA")
    tipo_observacion = models.CharField(
        max_length=15, choices=TIPO_OBSERVACION, default="OTRO"
    )
    descripcion = models.TextField()
    nivel_importancia = models.CharField(max_length=10, choices=NIVEL_ALERTA, default="BAJO")
    afecta_produccion = models.BooleanField(default=False)
    requiere_revision_tecnica = models.BooleanField(default=False)
    estado_observacion = models.CharField(
        max_length=20, choices=ESTADO_OBSERVACION, default="PENDIENTE"
    )
    id_lote = models.ForeignKey(
        "produccion.LoteProduccion", on_delete=models.DO_NOTHING, db_column="id_lote",
        blank=True, null=True, related_name="observaciones_diarias",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "observaciones_diarias"
        verbose_name = "Observación diaria"
        verbose_name_plural = "Observaciones diarias"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.tipo_observacion} - {self.id_maquina_id}"

    @property
    def badge_importancia(self):
        return {"BAJO": "secondary", "MEDIO": "info", "ALTO": "warning", "CRITICO": "danger"}.get(
            self.nivel_importancia, "secondary"
        )


class ReporteFalla(models.Model):
    URGENCIA = NIVEL_ALERTA
    ORIGEN = [
        ("CHECKLIST", "Checklist"),
        ("OBSERVACION_DIARIA", "Observación diaria"),
        ("PRODUCCION", "Producción"),
        ("MANTENIMIENTO", "Mantenimiento"),
        ("OTRO", "Otro"),
    ]
    ESTADO = [
        ("ABIERTO", "Abierto"),
        ("EN_REVISION", "En revisión"),
        ("CONVERTIDO_A_OT", "Convertido a OT"),
        ("CERRADO", "Cerrado"),
    ]

    id_reporte_falla = models.AutoField(primary_key=True)
    codigo_reporte = models.CharField(max_length=30, unique=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="reportes_falla",
    )
    id_usuario_reporta = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="id_usuario_reporta",
        related_name="reportes_falla",
    )
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    turno = models.CharField(max_length=10, choices=TURNO, default="MANANA")
    sintoma = models.CharField(max_length=150)
    descripcion_falla = models.TextField()
    nivel_urgencia = models.CharField(max_length=10, choices=URGENCIA, default="MEDIO")
    afecta_produccion = models.BooleanField(default=False)
    id_lote = models.ForeignKey(
        "produccion.LoteProduccion", on_delete=models.DO_NOTHING, db_column="id_lote",
        blank=True, null=True, related_name="reportes_falla",
    )
    origen_reporte = models.CharField(max_length=20, choices=ORIGEN, default="OTRO")
    estado_reporte = models.CharField(max_length=20, choices=ESTADO, default="ABIERTO")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "reportes_falla"
        verbose_name = "Reporte de falla"
        verbose_name_plural = "Reportes de falla"
        ordering = ["-fecha_reporte"]

    def __str__(self):
        return self.codigo_reporte

    @property
    def badge_estado(self):
        return {
            "ABIERTO": "danger", "EN_REVISION": "warning",
            "CONVERTIDO_A_OT": "info", "CERRADO": "success",
        }.get(self.estado_reporte, "secondary")


class PlanMantenimiento(models.Model):
    TIPO = [
        ("PREVENTIVO", "Preventivo"),
        ("PREDICTIVO", "Predictivo"),
        ("CALIBRACION", "Calibración"),
        ("LIMPIEZA_PROFUNDA", "Limpieza profunda"),
        ("INSPECCION", "Inspección"),
    ]
    FRECUENCIA = [
        ("DIARIO", "Diario"), ("SEMANAL", "Semanal"), ("MENSUAL", "Mensual"),
        ("TRIMESTRAL", "Trimestral"), ("SEMESTRAL", "Semestral"), ("ANUAL", "Anual"),
        ("POR_HORAS_USO", "Por horas de uso"),
    ]
    HORARIO = [
        ("ANTES_PRODUCCION", "Antes de producción"),
        ("FIN_JORNADA", "Fin de jornada"),
        ("FIN_SEMANA", "Fin de semana"),
        ("FUERA_TURNO", "Fuera de turno"),
        ("DIA_PARCIAL", "Día parcial"),
        ("CUANDO_APLIQUE", "Cuando aplique"),
    ]
    ESTADO = [
        ("ACTIVO", "Activo"), ("SUSPENDIDO", "Suspendido"),
        ("VENCIDO", "Vencido"), ("CERRADO", "Cerrado"),
    ]

    id_plan = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="planes",
    )
    tipo_mantenimiento = models.CharField(max_length=20, choices=TIPO, default="PREVENTIVO")
    actividad = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    frecuencia = models.CharField(max_length=15, choices=FRECUENCIA, default="SEMANAL")
    cada_horas_uso = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duracion_estimada_horas = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    requiere_parada = models.BooleanField(default=True)
    horario_recomendado = models.CharField(max_length=20, choices=HORARIO, default="FIN_JORNADA")
    responsable = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="responsable",
        blank=True, null=True, related_name="planes_responsable",
    )
    fecha_ultima_ejecucion = models.DateField(blank=True, null=True)
    fecha_proxima_ejecucion = models.DateField(blank=True, null=True)
    estado_plan = models.CharField(max_length=15, choices=ESTADO, default="ACTIVO")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "plan_mantenimiento"
        verbose_name = "Plan de mantenimiento"
        verbose_name_plural = "Planes de mantenimiento"
        ordering = ["fecha_proxima_ejecucion"]

    def __str__(self):
        return f"{self.actividad} ({self.tipo_mantenimiento})"


class OrdenTrabajo(models.Model):
    TIPO = [
        ("PREVENTIVA", "Preventiva"), ("CORRECTIVA", "Correctiva"),
        ("PREDICTIVA", "Predictiva"), ("CALIBRACION", "Calibración"),
        ("INSPECCION", "Inspección"),
    ]
    PRIORIDAD = [
        ("BAJA", "Baja"), ("MEDIA", "Media"), ("ALTA", "Alta"), ("CRITICA", "Crítica"),
    ]
    ESTADO = [
        ("PENDIENTE", "Pendiente"), ("PROGRAMADA", "Programada"),
        ("EN_EJECUCION", "En ejecución"), ("CERRADA", "Cerrada"), ("CANCELADA", "Cancelada"),
    ]
    TIPO_ATENCION = [
        ("EN_PLANTA", "En planta"), ("CAMBIO_PIEZA", "Cambio de pieza"),
        ("TALLER_EXTERNO", "Taller externo"), ("MAQUINA_ALTERNATIVA", "Máquina alternativa"),
        ("PENDIENTE_DEFINIR", "Pendiente definir"),
    ]

    id_ot = models.AutoField(primary_key=True)
    codigo_ot = models.CharField(max_length=30, unique=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="ordenes",
    )
    id_reporte_falla = models.ForeignKey(
        ReporteFalla, on_delete=models.DO_NOTHING, db_column="id_reporte_falla",
        blank=True, null=True, related_name="ordenes",
    )
    id_plan = models.ForeignKey(
        PlanMantenimiento, on_delete=models.DO_NOTHING, db_column="id_plan",
        blank=True, null=True, related_name="ordenes",
    )
    tipo_ot = models.CharField(max_length=15, choices=TIPO, default="PREVENTIVA")
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD, default="MEDIA")
    estado_ot = models.CharField(max_length=15, choices=ESTADO, default="PENDIENTE")
    descripcion_trabajo = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_programada = models.DateField(blank=True, null=True)
    hora_programada = models.TimeField(blank=True, null=True)
    fecha_inicio_real = models.DateTimeField(blank=True, null=True)
    fecha_fin_real = models.DateTimeField(blank=True, null=True)
    tiempo_parada_horas = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    responsable_tecnico = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="responsable_tecnico",
        blank=True, null=True, related_name="ordenes_tecnico",
    )
    requiere_repuesto = models.BooleanField(default=False)
    requiere_servicio_externo = models.BooleanField(default=False)
    tipo_atencion = models.CharField(
        max_length=20, choices=TIPO_ATENCION, default="PENDIENTE_DEFINIR"
    )
    costo_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_repuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_servicio_externo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    validado_por = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="validado_por",
        blank=True, null=True, related_name="ordenes_validadas",
    )
    observacion_cierre = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "ordenes_trabajo"
        verbose_name = "Orden de trabajo"
        verbose_name_plural = "Órdenes de trabajo"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.codigo_ot

    @property
    def badge_estado(self):
        return {
            "PENDIENTE": "warning", "PROGRAMADA": "info", "EN_EJECUCION": "primary",
            "CERRADA": "success", "CANCELADA": "secondary",
        }.get(self.estado_ot, "secondary")


class DetalleOrdenTrabajo(models.Model):
    RESULTADO_PRUEBA = [
        ("APROBADO", "Aprobado"), ("OBSERVADO", "Observado"),
        ("NO_APROBADO", "No aprobado"), ("NO_APLICA", "No aplica"),
    ]

    id_detalle_ot = models.AutoField(primary_key=True)
    id_ot = models.ForeignKey(
        OrdenTrabajo, on_delete=models.DO_NOTHING, db_column="id_ot",
        related_name="detalles",
    )
    actividad_realizada = models.TextField()
    diagnostico = models.TextField(blank=True, null=True)
    causa_raiz = models.TextField(blank=True, null=True)
    accion_correctiva = models.TextField(blank=True, null=True)
    resultado_prueba = models.CharField(
        max_length=15, choices=RESULTADO_PRUEBA, default="NO_APLICA"
    )
    tiempo_ejecucion_horas = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "detalle_orden_trabajo"
        verbose_name = "Detalle de OT"
        verbose_name_plural = "Detalles de OT"

    def __str__(self):
        return f"Detalle OT {self.id_ot_id}"


class MedicionOperativa(models.Model):
    id_medicion = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="mediciones",
    )
    id_lote = models.ForeignKey(
        "produccion.LoteProduccion", on_delete=models.DO_NOTHING, db_column="id_lote",
        blank=True, null=True, related_name="mediciones",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    temperatura = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vibracion = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ruido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    amperaje = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    presion = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    velocidad = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "mediciones_operativas"
        verbose_name = "Medición operativa"
        verbose_name_plural = "Mediciones operativas"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"Medición {self.id_maquina_id} {self.fecha_hora}"
