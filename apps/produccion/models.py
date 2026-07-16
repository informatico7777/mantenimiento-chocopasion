"""Modelos de producción y energía: lotes y consumo energético."""
from django.db import models


class LoteProduccion(models.Model):
    ESTADO = [
        ("PROGRAMADO", "Programado"), ("EN_PROCESO", "En proceso"),
        ("DETENIDO", "Detenido"), ("FINALIZADO", "Finalizado"), ("ANULADO", "Anulado"),
    ]

    id_lote = models.AutoField(primary_key=True)
    codigo_lote = models.CharField(max_length=50, unique=True)
    fecha_produccion = models.DateField()
    producto = models.CharField(max_length=100)
    kg_cacao_ingresado = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    kg_producto_final = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    responsable_produccion = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="responsable_produccion",
        blank=True, null=True, related_name="lotes",
    )
    estado_lote = models.CharField(max_length=15, choices=ESTADO, default="PROGRAMADO")
    observaciones = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "lotes_produccion"
        verbose_name = "Lote de producción"
        verbose_name_plural = "Lotes de producción"
        ordering = ["-fecha_produccion"]

    def __str__(self):
        return self.codigo_lote


class ConsumoEnergetico(models.Model):
    TIPO_ENERGIA = [
        ("ELECTRICIDAD", "Electricidad"), ("GLP", "GLP"), ("NEUMATICA", "Neumática"),
        ("MIXTA", "Mixta"), ("BATERIA", "Batería"), ("NO_APLICA", "No aplica"),
    ]

    id_consumo = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="consumos",
    )
    id_lote = models.ForeignKey(
        LoteProduccion, on_delete=models.DO_NOTHING, db_column="id_lote",
        blank=True, null=True, related_name="consumos",
    )
    fecha = models.DateField()
    tipo_energia = models.CharField(max_length=15, choices=TIPO_ENERGIA, default="ELECTRICIDAD")
    potencia_kw = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    horas_uso = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    kwh_estimado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    glp_estimado_kg = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    costo_unitario_energia = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    costo_total_energia = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    observacion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "consumo_energetico"
        verbose_name = "Consumo energético"
        verbose_name_plural = "Consumos energéticos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Consumo {self.id_maquina_id} {self.fecha}"
