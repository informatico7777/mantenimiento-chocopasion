from django import forms

from .models import MovimientoRepuesto, Proveedor, Repuesto, ServicioExterno

INP = {"class": "form-control"}
SEL = {"class": "form-select"}


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre_proveedor", "ruc", "tipo_proveedor", "telefono",
                  "correo", "direccion", "observaciones", "estado"]
        widgets = {
            "nombre_proveedor": forms.TextInput(attrs=INP),
            "ruc": forms.TextInput(attrs=INP),
            "tipo_proveedor": forms.Select(attrs=SEL),
            "telefono": forms.TextInput(attrs=INP),
            "correo": forms.EmailInput(attrs=INP),
            "direccion": forms.TextInput(attrs=INP),
            "observaciones": forms.Textarea(attrs={**INP, "rows": 2}),
            "estado": forms.Select(attrs=SEL),
        }


class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = ["codigo_repuesto", "nombre_repuesto", "descripcion", "unidad_medida",
                  "stock_actual", "stock_minimo", "stock_maximo", "costo_unitario",
                  "id_proveedor", "ubicacion_almacen", "estado"]
        widgets = {
            "codigo_repuesto": forms.TextInput(attrs=INP),
            "nombre_repuesto": forms.TextInput(attrs=INP),
            "descripcion": forms.Textarea(attrs={**INP, "rows": 2}),
            "unidad_medida": forms.TextInput(attrs=INP),
            "stock_actual": forms.NumberInput(attrs=INP),
            "stock_minimo": forms.NumberInput(attrs=INP),
            "stock_maximo": forms.NumberInput(attrs=INP),
            "costo_unitario": forms.NumberInput(attrs=INP),
            "id_proveedor": forms.Select(attrs=SEL),
            "ubicacion_almacen": forms.TextInput(attrs=INP),
            "estado": forms.Select(attrs=SEL),
        }


class MovimientoRepuestoForm(forms.ModelForm):
    class Meta:
        model = MovimientoRepuesto
        fields = ["tipo_movimiento", "cantidad", "id_ot", "costo_total", "observacion"]
        widgets = {
            "tipo_movimiento": forms.Select(attrs=SEL),
            "cantidad": forms.NumberInput(attrs=INP),
            "id_ot": forms.Select(attrs=SEL),
            "costo_total": forms.NumberInput(attrs=INP),
            "observacion": forms.Textarea(attrs={**INP, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_ot"].required = False

    def clean_cantidad(self):
        cantidad = self.cleaned_data["cantidad"]
        if cantidad is None or cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad


class ServicioExternoForm(forms.ModelForm):
    class Meta:
        model = ServicioExterno
        fields = ["id_ot", "id_maquina", "motivo_envio", "id_proveedor", "fecha_salida",
                  "fecha_retorno_estimada", "fecha_retorno_real", "costo_servicio",
                  "diagnostico_externo", "estado_servicio"]
        widgets = {
            "id_ot": forms.Select(attrs=SEL),
            "id_maquina": forms.Select(attrs=SEL),
            "motivo_envio": forms.Textarea(attrs={**INP, "rows": 2}),
            "id_proveedor": forms.Select(attrs=SEL),
            "fecha_salida": forms.DateInput(attrs={**INP, "type": "date"}),
            "fecha_retorno_estimada": forms.DateInput(attrs={**INP, "type": "date"}),
            "fecha_retorno_real": forms.DateInput(attrs={**INP, "type": "date"}),
            "costo_servicio": forms.NumberInput(attrs=INP),
            "diagnostico_externo": forms.Textarea(attrs={**INP, "rows": 2}),
            "estado_servicio": forms.Select(attrs=SEL),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for c in ["fecha_retorno_estimada", "fecha_retorno_real", "diagnostico_externo"]:
            self.fields[c].required = False


class MaquinaRepuestoForm(forms.ModelForm):
    """Relación de repuesto crítico con una máquina (tabla maquina_repuesto)."""

    class Meta:
        from .models import MaquinaRepuesto

        model = MaquinaRepuesto
        fields = [
            "id_repuesto", "cantidad_recomendada_stock", "criticidad_repuesto",
            "tiempo_reposicion_dias", "observacion",
        ]
        widgets = {
            "id_repuesto": forms.Select(attrs=SEL),
            "cantidad_recomendada_stock": forms.NumberInput(attrs=INP),
            "criticidad_repuesto": forms.Select(attrs=SEL),
            "tiempo_reposicion_dias": forms.NumberInput(attrs=INP),
            "observacion": forms.Textarea(attrs={**INP, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tiempo_reposicion_dias"].required = False
        self.fields["observacion"].required = False
        self.fields["id_repuesto"].queryset = Repuesto.objects.order_by("nombre_repuesto")
