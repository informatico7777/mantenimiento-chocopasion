from django import forms

from .models import (
    ChecklistEjecucion,
    ChecklistPlantilla,
    DetalleOrdenTrabajo,
    ObservacionDiaria,
    OrdenTrabajo,
    ReporteFalla,
)

INP = {"class": "form-control"}
SEL = {"class": "form-select"}
CHK = {"class": "form-check-input"}


class ChecklistPlantillaForm(forms.ModelForm):
    class Meta:
        model = ChecklistPlantilla
        fields = [
            "id_maquina", "pregunta", "tipo_respuesta", "valor_minimo", "valor_maximo",
            "unidad_medida", "obligatorio", "bloquea_produccion", "frecuencia",
            "estado", "orden_visualizacion",
        ]
        widgets = {
            "id_maquina": forms.Select(attrs=SEL),
            "pregunta": forms.Textarea(attrs={**INP, "rows": 2}),
            "tipo_respuesta": forms.Select(attrs=SEL),
            "valor_minimo": forms.NumberInput(attrs=INP),
            "valor_maximo": forms.NumberInput(attrs=INP),
            "unidad_medida": forms.TextInput(attrs=INP),
            "obligatorio": forms.CheckboxInput(attrs=CHK),
            "bloquea_produccion": forms.CheckboxInput(attrs=CHK),
            "frecuencia": forms.Select(attrs=SEL),
            "estado": forms.Select(attrs=SEL),
            "orden_visualizacion": forms.NumberInput(attrs=INP),
        }


class ChecklistEjecucionForm(forms.ModelForm):
    class Meta:
        model = ChecklistEjecucion
        fields = ["fecha", "turno", "hora_inicio", "hora_fin",
                  "observacion_general", "firma_responsable"]
        widgets = {
            "fecha": forms.DateInput(attrs={**INP, "type": "date"}),
            "turno": forms.Select(attrs=SEL),
            "hora_inicio": forms.TimeInput(attrs={**INP, "type": "time"}),
            "hora_fin": forms.TimeInput(attrs={**INP, "type": "time"}),
            "observacion_general": forms.Textarea(attrs={**INP, "rows": 2}),
            "firma_responsable": forms.TextInput(attrs=INP),
        }


class ObservacionDiariaForm(forms.ModelForm):
    class Meta:
        model = ObservacionDiaria
        fields = [
            "id_maquina", "turno", "tipo_observacion", "descripcion",
            "nivel_importancia", "afecta_produccion", "requiere_revision_tecnica",
            "id_lote",
        ]
        widgets = {
            "id_maquina": forms.Select(attrs=SEL),
            "turno": forms.Select(attrs=SEL),
            "tipo_observacion": forms.Select(attrs=SEL),
            "descripcion": forms.Textarea(attrs={**INP, "rows": 3}),
            "nivel_importancia": forms.Select(attrs=SEL),
            "afecta_produccion": forms.CheckboxInput(attrs=CHK),
            "requiere_revision_tecnica": forms.CheckboxInput(attrs=CHK),
            "id_lote": forms.Select(attrs=SEL),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_lote"].required = False


class ReporteFallaForm(forms.ModelForm):
    class Meta:
        model = ReporteFalla
        fields = [
            "id_maquina", "turno", "sintoma", "descripcion_falla", "nivel_urgencia",
            "afecta_produccion", "id_lote", "origen_reporte",
        ]
        widgets = {
            "id_maquina": forms.Select(attrs=SEL),
            "turno": forms.Select(attrs=SEL),
            "sintoma": forms.TextInput(attrs=INP),
            "descripcion_falla": forms.Textarea(attrs={**INP, "rows": 3}),
            "nivel_urgencia": forms.Select(attrs=SEL),
            "afecta_produccion": forms.CheckboxInput(attrs=CHK),
            "id_lote": forms.Select(attrs=SEL),
            "origen_reporte": forms.Select(attrs=SEL),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_lote"].required = False


class OrdenTrabajoForm(forms.ModelForm):
    class Meta:
        model = OrdenTrabajo
        fields = [
            "id_maquina", "id_reporte_falla", "id_plan", "tipo_ot", "prioridad",
            "estado_ot", "descripcion_trabajo", "fecha_programada", "hora_programada",
            "fecha_inicio_real", "fecha_fin_real", "tiempo_parada_horas",
            "responsable_tecnico", "requiere_repuesto", "requiere_servicio_externo",
            "tipo_atencion", "costo_mano_obra", "costo_repuestos",
            "costo_servicio_externo", "validado_por", "observacion_cierre",
        ]
        widgets = {
            "id_maquina": forms.Select(attrs=SEL),
            "id_reporte_falla": forms.Select(attrs=SEL),
            "id_plan": forms.Select(attrs=SEL),
            "tipo_ot": forms.Select(attrs=SEL),
            "prioridad": forms.Select(attrs=SEL),
            "estado_ot": forms.Select(attrs=SEL),
            "descripcion_trabajo": forms.Textarea(attrs={**INP, "rows": 3}),
            "fecha_programada": forms.DateInput(attrs={**INP, "type": "date"}),
            "hora_programada": forms.TimeInput(attrs={**INP, "type": "time"}),
            "fecha_inicio_real": forms.DateTimeInput(
                attrs={**INP, "type": "datetime-local"}
            ),
            "fecha_fin_real": forms.DateTimeInput(
                attrs={**INP, "type": "datetime-local"}
            ),
            "tiempo_parada_horas": forms.NumberInput(attrs=INP),
            "responsable_tecnico": forms.Select(attrs=SEL),
            "requiere_repuesto": forms.CheckboxInput(attrs=CHK),
            "requiere_servicio_externo": forms.CheckboxInput(attrs=CHK),
            "tipo_atencion": forms.Select(attrs=SEL),
            "costo_mano_obra": forms.NumberInput(attrs=INP),
            "costo_repuestos": forms.NumberInput(attrs=INP),
            "costo_servicio_externo": forms.NumberInput(attrs=INP),
            "validado_por": forms.Select(attrs=SEL),
            "observacion_cierre": forms.Textarea(attrs={**INP, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ["id_reporte_falla", "id_plan", "responsable_tecnico",
                      "validado_por", "fecha_programada", "hora_programada",
                      "fecha_inicio_real", "fecha_fin_real", "tiempo_parada_horas",
                      "observacion_cierre"]:
            self.fields[campo].required = False


class DetalleOrdenTrabajoForm(forms.ModelForm):
    class Meta:
        model = DetalleOrdenTrabajo
        fields = [
            "actividad_realizada", "diagnostico", "causa_raiz", "accion_correctiva",
            "resultado_prueba", "tiempo_ejecucion_horas", "observaciones",
        ]
        widgets = {
            "actividad_realizada": forms.Textarea(attrs={**INP, "rows": 2}),
            "diagnostico": forms.Textarea(attrs={**INP, "rows": 2}),
            "causa_raiz": forms.Textarea(attrs={**INP, "rows": 2}),
            "accion_correctiva": forms.Textarea(attrs={**INP, "rows": 2}),
            "resultado_prueba": forms.Select(attrs=SEL),
            "tiempo_ejecucion_horas": forms.NumberInput(attrs=INP),
            "observaciones": forms.Textarea(attrs={**INP, "rows": 2}),
        }
