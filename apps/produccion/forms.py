from django import forms

from .models import ConsumoEnergetico, LoteProduccion

INP = {"class": "form-control"}
SEL = {"class": "form-select"}


class LoteProduccionForm(forms.ModelForm):
    class Meta:
        model = LoteProduccion
        fields = ["codigo_lote", "fecha_produccion", "producto", "kg_cacao_ingresado",
                  "kg_producto_final", "responsable_produccion", "estado_lote",
                  "observaciones"]
        widgets = {
            "codigo_lote": forms.TextInput(attrs=INP),
            "fecha_produccion": forms.DateInput(attrs={**INP, "type": "date"}),
            "producto": forms.TextInput(attrs=INP),
            "kg_cacao_ingresado": forms.NumberInput(attrs=INP),
            "kg_producto_final": forms.NumberInput(attrs=INP),
            "responsable_produccion": forms.Select(attrs=SEL),
            "estado_lote": forms.Select(attrs=SEL),
            "observaciones": forms.Textarea(attrs={**INP, "rows": 2}),
        }


class ConsumoEnergeticoForm(forms.ModelForm):
    class Meta:
        model = ConsumoEnergetico
        fields = ["id_maquina", "id_lote", "fecha", "tipo_energia", "potencia_kw",
                  "horas_uso", "kwh_estimado", "glp_estimado_kg",
                  "costo_unitario_energia", "costo_total_energia", "observacion"]
        widgets = {
            "id_maquina": forms.Select(attrs=SEL),
            "id_lote": forms.Select(attrs=SEL),
            "fecha": forms.DateInput(attrs={**INP, "type": "date"}),
            "tipo_energia": forms.Select(attrs=SEL),
            "potencia_kw": forms.NumberInput(attrs=INP),
            "horas_uso": forms.NumberInput(attrs=INP),
            "kwh_estimado": forms.NumberInput(attrs=INP),
            "glp_estimado_kg": forms.NumberInput(attrs=INP),
            "costo_unitario_energia": forms.NumberInput(attrs=INP),
            "costo_total_energia": forms.NumberInput(attrs=INP),
            "observacion": forms.Textarea(attrs={**INP, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_lote"].required = False
