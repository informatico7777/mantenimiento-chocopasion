"""Modelos de reportes, indicadores y auditoría."""
from django.db import models
from config.base_model import MANAGED


class ReporteGenerado(models.Model):
    TIPO = [
        ("DIARIO", "Diario"), ("SEMANAL", "Semanal"), ("MENSUAL", "Mensual"),
        ("POR_MAQUINA", "Por máquina"), ("POR_AREA", "Por área"),
        ("POR_OT", "Por OT"), ("PERSONALIZADO", "Personalizado"),
    ]
    FORMATO = [("PDF", "PDF"), ("EXCEL", "Excel"), ("CSV", "CSV")]
    ESTADO = [("GENERADO", "Generado"), ("DESCARGADO", "Descargado"), ("ANULADO", "Anulado")]

    id_reporte_generado = models.AutoField(primary_key=True)
    codigo_reporte = models.CharField(max_length=50, unique=True)
    tipo_reporte = models.CharField(max_length=15, choices=TIPO, default="SEMANAL")
    titulo_reporte = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    id_area = models.ForeignKey(
        "core.Area", on_delete=models.DO_NOTHING, db_column="id_area",
        blank=True, null=True, related_name="reportes",
    )
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        blank=True, null=True, related_name="reportes",
    )
    generado_por = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="generado_por",
        related_name="reportes_generados",
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    formato = models.CharField(max_length=10, choices=FORMATO, default="PDF")
    ruta_archivo = models.CharField(max_length=255)
    descargable = models.BooleanField(default=True)
    resumen = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO, default="GENERADO")

    class Meta:
        managed = MANAGED
        db_table = "reportes_generados"
        verbose_name = "Reporte generado"
        verbose_name_plural = "Reportes generados"
        ordering = ["-fecha_generacion"]

    def __str__(self):
        return self.codigo_reporte


class DetalleReporteGenerado(models.Model):
    TIPO_REGISTRO = [
        ("CHECKLIST", "Checklist"), ("OBSERVACION", "Observación"), ("FALLA", "Falla"),
        ("OT", "Orden de trabajo"), ("CONSUMO", "Consumo"), ("REPUESTO", "Repuesto"),
        ("MAQUINA", "Máquina"), ("INDICADOR", "Indicador"), ("OTRO", "Otro"),
    ]

    id_detalle_reporte = models.AutoField(primary_key=True)
    id_reporte_generado = models.ForeignKey(
        ReporteGenerado, on_delete=models.DO_NOTHING, db_column="id_reporte_generado",
        related_name="detalles",
    )
    tipo_registro = models.CharField(max_length=15, choices=TIPO_REGISTRO)
    id_registro = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED
        db_table = "detalle_reportes_generados"
        verbose_name = "Detalle de reporte generado"
        verbose_name_plural = "Detalles de reportes generados"

    def __str__(self):
        return f"{self.tipo_registro} #{self.id_registro}"


class IndicadorMantenimiento(models.Model):
    id_indicador = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="indicadores",
    )
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    horas_programadas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    horas_parada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    disponibilidad_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    numero_fallas = models.IntegerField(default=0)
    mtbf_horas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mttr_horas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cumplimiento_preventivo = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    costo_mantenimiento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    consumo_energia_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "indicadores_mantenimiento"
        verbose_name = "Indicador de mantenimiento"
        verbose_name_plural = "Indicadores de mantenimiento"
        ordering = ["-periodo_fin"]

    def __str__(self):
        return f"Indicador {self.id_maquina_id} {self.periodo_inicio}-{self.periodo_fin}"


class AuditoriaSistema(models.Model):
    ACCION = [
        ("CREAR", "Crear"), ("EDITAR", "Editar"), ("ELIMINAR", "Eliminar"),
        ("DESCARGAR", "Descargar"), ("GENERAR_REPORTE", "Generar reporte"),
        ("LOGIN", "Login"), ("LOGOUT", "Logout"), ("OTRO", "Otro"),
    ]

    id_auditoria = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="id_usuario",
        blank=True, null=True, related_name="auditorias",
    )
    tabla_afectada = models.CharField(max_length=100)
    id_registro_afectado = models.IntegerField(blank=True, null=True)
    accion = models.CharField(max_length=20, choices=ACCION, default="OTRO")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = MANAGED
        db_table = "auditoria_sistema"
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditoría del sistema"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.accion} {self.tabla_afectada} #{self.id_registro_afectado}"
