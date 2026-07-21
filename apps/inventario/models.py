"""Modelos de inventario: proveedores, repuestos, movimientos y servicios externos."""
from django.db import models

from apps.core.choices import CRITICIDAD
from config.base_model import MANAGED


class Proveedor(models.Model):
    TIPO = [
        ("REPUESTOS", "Repuestos"), ("TALLER", "Taller"), ("CALIBRACION", "Calibración"),
        ("REFRIGERACION", "Refrigeración"), ("ELECTRICO", "Eléctrico"),
        ("MECANICO", "Mecánico"), ("GAS", "Gas"), ("OTRO", "Otro"),
    ]
    ESTADO = [("ACTIVO", "Activo"), ("INACTIVO", "Inactivo")]

    id_proveedor = models.AutoField(primary_key=True)
    nombre_proveedor = models.CharField(max_length=150)
    ruc = models.CharField(max_length=20, blank=True, null=True, unique=True)
    tipo_proveedor = models.CharField(max_length=15, choices=TIPO, default="OTRO")
    telefono = models.CharField(max_length=30, blank=True, null=True)
    correo = models.EmailField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO, default="ACTIVO")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "proveedores"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre_proveedor"]

    def __str__(self):
        return self.nombre_proveedor


class Repuesto(models.Model):
    ESTADO = [
        ("DISPONIBLE", "Disponible"), ("AGOTADO", "Agotado"),
        ("OBSOLETO", "Obsoleto"), ("INACTIVO", "Inactivo"),
    ]

    id_repuesto = models.AutoField(primary_key=True)
    codigo_repuesto = models.CharField(max_length=50, unique=True)
    nombre_repuesto = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    unidad_medida = models.CharField(max_length=30, default="UNIDAD")
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_maximo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    id_proveedor = models.ForeignKey(
        Proveedor, on_delete=models.DO_NOTHING, db_column="id_proveedor",
        blank=True, null=True, related_name="repuestos",
    )
    ubicacion_almacen = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO, default="DISPONIBLE")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "repuestos"
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"
        ordering = ["nombre_repuesto"]

    def __str__(self):
        return f"{self.codigo_repuesto} - {self.nombre_repuesto}"

    @property
    def bajo_stock(self):
        return self.stock_actual <= self.stock_minimo


class MaquinaRepuesto(models.Model):
    CRITICIDAD_REPUESTO = [
        ("BAJA", "Baja"), ("MEDIA", "Media"), ("ALTA", "Alta"), ("CRITICA", "Crítica"),
    ]

    id_maquina_repuesto = models.AutoField(primary_key=True)
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="repuestos_asociados",
    )
    id_repuesto = models.ForeignKey(
        Repuesto, on_delete=models.DO_NOTHING, db_column="id_repuesto",
        related_name="maquinas_asociadas",
    )
    cantidad_recomendada_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=1
    )
    criticidad_repuesto = models.CharField(
        max_length=10, choices=CRITICIDAD_REPUESTO, default="MEDIA"
    )
    tiempo_reposicion_dias = models.IntegerField(blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED
        db_table = "maquina_repuesto"
        verbose_name = "Repuesto por máquina"
        verbose_name_plural = "Repuestos por máquina"

    def __str__(self):
        return f"{self.id_maquina_id} - {self.id_repuesto_id}"


class MovimientoRepuesto(models.Model):
    TIPO = [
        ("ENTRADA", "Entrada"), ("SALIDA", "Salida"),
        ("AJUSTE_POSITIVO", "Ajuste positivo"), ("AJUSTE_NEGATIVO", "Ajuste negativo"),
        ("DEVOLUCION", "Devolución"),
    ]

    id_movimiento = models.AutoField(primary_key=True)
    id_repuesto = models.ForeignKey(
        Repuesto, on_delete=models.DO_NOTHING, db_column="id_repuesto",
        related_name="movimientos",
    )
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    id_ot = models.ForeignKey(
        "mantenimiento.OrdenTrabajo", on_delete=models.DO_NOTHING, db_column="id_ot",
        blank=True, null=True, related_name="movimientos_repuesto",
    )
    responsable = models.ForeignKey(
        "accounts.Usuario", on_delete=models.DO_NOTHING, db_column="responsable",
        related_name="movimientos_repuesto",
    )
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = MANAGED
        db_table = "movimiento_repuestos"
        verbose_name = "Movimiento de repuesto"
        verbose_name_plural = "Movimientos de repuestos"
        ordering = ["-fecha_movimiento"]

    def __str__(self):
        return f"{self.tipo_movimiento} {self.cantidad} ({self.id_repuesto_id})"


class ServicioExterno(models.Model):
    ESTADO = [
        ("ENVIADO", "Enviado"), ("EN_REPARACION", "En reparación"),
        ("RETORNADO", "Retornado"), ("CERRADO", "Cerrado"), ("CANCELADO", "Cancelado"),
    ]

    id_servicio_externo = models.AutoField(primary_key=True)
    id_ot = models.ForeignKey(
        "mantenimiento.OrdenTrabajo", on_delete=models.DO_NOTHING, db_column="id_ot",
        related_name="servicios_externos",
    )
    id_maquina = models.ForeignKey(
        "core.Maquina", on_delete=models.DO_NOTHING, db_column="id_maquina",
        related_name="servicios_externos",
    )
    motivo_envio = models.TextField()
    id_proveedor = models.ForeignKey(
        Proveedor, on_delete=models.DO_NOTHING, db_column="id_proveedor",
        related_name="servicios_externos",
    )
    fecha_salida = models.DateField()
    fecha_retorno_estimada = models.DateField(blank=True, null=True)
    fecha_retorno_real = models.DateField(blank=True, null=True)
    costo_servicio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diagnostico_externo = models.TextField(blank=True, null=True)
    estado_servicio = models.CharField(max_length=15, choices=ESTADO, default="ENVIADO")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        managed = MANAGED
        db_table = "servicios_externos"
        verbose_name = "Servicio externo"
        verbose_name_plural = "Servicios externos"
        ordering = ["-fecha_salida"]

    def __str__(self):
        return f"Servicio OT {self.id_ot_id} - {self.id_proveedor_id}"
