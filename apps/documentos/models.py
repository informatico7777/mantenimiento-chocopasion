"""Modelo de archivos adjuntos."""
from django.db import models
from config.base_model import MANAGED


class ArchivoAdjunto(models.Model):
    TIPO_ENTIDAD = [
        ("MAQUINA", "Máquina"), ("CHECKLIST", "Checklist"), ("FALLA", "Falla"),
        ("OT", "Orden de trabajo"), ("REPUESTO", "Repuesto"),
        ("SERVICIO_EXTERNO", "Servicio externo"), ("REPORTE", "Reporte"),
        ("OBSERVACION", "Observación"), ("OTRO", "Otro"),
    ]
    CATEGORIA = [
        ("FOTO_MAQUINA", "Foto de máquina"), ("PLACA_TECNICA", "Placa técnica"),
        ("FICHA_TECNICA", "Ficha técnica"), ("MANUAL", "Manual"),
        ("EVIDENCIA", "Evidencia"), ("PDF", "PDF"), ("INFORME", "Informe"), ("OTRO", "Otro"),
    ]
    TIPO_ARCHIVO = [
        ("JPG", "JPG"), ("JPEG", "JPEG"), ("PNG", "PNG"), ("PDF", "PDF"),
        ("DOCX", "DOCX"), ("XLSX", "XLSX"), ("CSV", "CSV"), ("TXT", "TXT"), ("OTRO", "Otro"),
    ]
    ESTADO = [("ACTIVO", "Activo"), ("ELIMINADO", "Eliminado")]

    id_adjunto = models.AutoField(primary_key=True)
    tipo_entidad = models.CharField(max_length=20, choices=TIPO_ENTIDAD)
    id_entidad = models.IntegerField()
    categoria_archivo = models.CharField(max_length=20, choices=CATEGORIA, default="OTRO")
    nombre_archivo = models.CharField(max_length=200)
    tipo_archivo = models.CharField(max_length=10, choices=TIPO_ARCHIVO, default="OTRO")
    ruta_archivo = models.CharField(max_length=255)
    descargable = models.BooleanField(default=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="subido_por",
        related_name="archivos_subidos",
    )
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO, default="ACTIVO")

    class Meta:
        managed = MANAGED
        db_table = "archivos_adjuntos"
        verbose_name = "Archivo adjunto"
        verbose_name_plural = "Archivos adjuntos"
        ordering = ["-fecha_subida"]

    def __str__(self):
        return self.nombre_archivo

    @property
    def es_imagen(self):
        return self.tipo_archivo in ("JPG", "JPEG", "PNG")
