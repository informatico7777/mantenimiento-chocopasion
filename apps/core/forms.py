from django import forms

from .models import Area, Maquina

BOOTSTRAP_INPUT = {"class": "form-control"}
BOOTSTRAP_SELECT = {"class": "form-select"}
BOOTSTRAP_CHECK = {"class": "form-check-input"}


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["nombre_area", "descripcion", "responsable_area", "estado"]
        widgets = {
            "nombre_area": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "descripcion": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 3}),
            "responsable_area": forms.Select(attrs=BOOTSTRAP_SELECT),
            "estado": forms.Select(attrs=BOOTSTRAP_SELECT),
        }


class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = [
            "codigo_activo", "nombre_maquina", "tipo_maquina", "id_area",
            "marca", "modelo", "numero_serie", "capacidad_valor", "capacidad_unidad",
            "tipo_energia", "potencia_kw", "potencia_hp", "consumo_estimado_hora",
            "consumo_estimado_lote", "criticidad", "estado_operativo",
            "ubicacion_fisica", "fecha_instalacion", "responsable_maquina",
            "requiere_checklist_diario", "requiere_calibracion", "observaciones",
        ]
        widgets = {
            "codigo_activo": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "nombre_maquina": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "tipo_maquina": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "id_area": forms.Select(attrs=BOOTSTRAP_SELECT),
            "marca": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "modelo": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "numero_serie": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "capacidad_valor": forms.NumberInput(attrs=BOOTSTRAP_INPUT),
            "capacidad_unidad": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "tipo_energia": forms.Select(attrs=BOOTSTRAP_SELECT),
            "potencia_kw": forms.NumberInput(attrs=BOOTSTRAP_INPUT),
            "potencia_hp": forms.NumberInput(attrs=BOOTSTRAP_INPUT),
            "consumo_estimado_hora": forms.NumberInput(attrs=BOOTSTRAP_INPUT),
            "consumo_estimado_lote": forms.NumberInput(attrs=BOOTSTRAP_INPUT),
            "criticidad": forms.Select(attrs=BOOTSTRAP_SELECT),
            "estado_operativo": forms.Select(attrs=BOOTSTRAP_SELECT),
            "ubicacion_fisica": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "fecha_instalacion": forms.DateInput(
                attrs={**BOOTSTRAP_INPUT, "type": "date"}
            ),
            "responsable_maquina": forms.Select(attrs=BOOTSTRAP_SELECT),
            "requiere_checklist_diario": forms.CheckboxInput(attrs=BOOTSTRAP_CHECK),
            "requiere_calibracion": forms.CheckboxInput(attrs=BOOTSTRAP_CHECK),
            "observaciones": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_area"].queryset = Area.objects.filter(estado="ACTIVA")


class AuditoriaFiltroForm(forms.Form):
    """Filtros de la pantalla de auditoría del sistema."""

    usuario = forms.ModelChoiceField(
        label="Usuario", queryset=None, required=False,
        empty_label="Todos", widget=forms.Select(attrs=BOOTSTRAP_SELECT),
    )
    accion = forms.ChoiceField(
        label="Acción", required=False, widget=forms.Select(attrs=BOOTSTRAP_SELECT),
    )
    tabla = forms.ChoiceField(
        label="Tabla afectada", required=False, widget=forms.Select(attrs=BOOTSTRAP_SELECT),
    )
    fecha_inicio = forms.DateField(
        label="Desde", required=False,
        widget=forms.DateInput(attrs={**BOOTSTRAP_INPUT, "type": "date"}),
    )
    fecha_fin = forms.DateField(
        label="Hasta", required=False,
        widget=forms.DateInput(attrs={**BOOTSTRAP_INPUT, "type": "date"}),
    )
    q = forms.CharField(
        label="Buscar en descripción", required=False,
        widget=forms.TextInput(attrs={**BOOTSTRAP_INPUT, "placeholder": "Texto en la descripción"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import Usuario

        from .auditoria import ACCIONES, tablas_disponibles

        self.fields["usuario"].queryset = Usuario.objects.order_by("apellidos", "nombres")
        self.fields["accion"].choices = [("", "Todas")] + ACCIONES
        self.fields["tabla"].choices = [("", "Todas")] + [
            (t, t) for t in tablas_disponibles()
        ]


# =====================================================================
# CRUD de componentes de máquina y fallas probables
# =====================================================================
from .models import ComponenteMaquina, FallaProbable  # noqa: E402

# Orden de severidad de los niveles de riesgo (para no degradar el nivel).
_ORDEN_RIESGO = {"BAJO": 0, "MEDIO": 1, "ALTO": 2, "CRITICO": 3}
_RIESGO_POR_INDICE = ["BAJO", "MEDIO", "ALTO", "CRITICO"]


def _nivel_severidad(severidad):
    """La severidad se guarda como entero 1-10; se traduce a BAJA/MEDIA/ALTA."""
    if severidad is None:
        return "MEDIA"
    s = int(severidad)
    if s >= 7:
        return "ALTA"
    if s >= 4:
        return "MEDIA"
    return "BAJA"


def _subir_un_nivel(riesgo):
    idx = min(_ORDEN_RIESGO.get(riesgo, 1) + 1, 3)
    return _RIESGO_POR_INDICE[idx]


def sugerir_nivel_riesgo(nivel_probabilidad, severidad, detectabilidad):
    """
    Sugiere el nivel de riesgo (BAJO/MEDIO/ALTO/CRITICO) según la matriz
    severidad × probabilidad. La severidad (entero 1-10) se traduce a nivel
    (ALTA>=7, MEDIA 4-6, BAJA 1-3) para no cambiar la base de datos.

    Matriz:
      - Sev ALTA  + Prob ALTA/MUY_ALTA -> CRITICO
      - Sev ALTA  + Prob MEDIA         -> ALTO
      - Sev MEDIA + Prob ALTA/MUY_ALTA -> ALTO
      - Sev MEDIA + Prob MEDIA         -> MEDIO
      - Sev BAJA  + Prob BAJA          -> BAJO
      - Resto de combinaciones         -> valor intermedio razonable
    Además: si la detectabilidad es baja (<=3, difícil de detectar), se eleva
    un nivel de riesgo.
    """
    sev = _nivel_severidad(severidad)
    prob = nivel_probabilidad or "MEDIA"
    prob_alta = prob in ("ALTA", "MUY_ALTA")
    prob_media = prob == "MEDIA"

    if sev == "ALTA" and prob_alta:
        riesgo = "CRITICO"
    elif sev == "ALTA" and prob_media:
        riesgo = "ALTO"
    elif sev == "MEDIA" and prob_alta:
        riesgo = "ALTO"
    elif sev == "MEDIA" and prob_media:
        riesgo = "MEDIO"
    elif sev == "BAJA" and prob == "BAJA":
        riesgo = "BAJO"
    elif sev == "ALTA":            # prob BAJA
        riesgo = "MEDIO"
    elif sev == "BAJA" and prob_alta:
        riesgo = "MEDIO"
    else:                          # BAJA+MEDIA, MEDIA+BAJA
        riesgo = "BAJO"

    # Detectabilidad baja (difícil de detectar) eleva el riesgo un nivel.
    if detectabilidad is not None and int(detectabilidad) <= 3:
        riesgo = _subir_un_nivel(riesgo)

    return riesgo


def combinar_riesgo(elegido, sugerido):
    """Devuelve el mayor entre el nivel elegido por el usuario y el sugerido."""
    if not elegido:
        return sugerido
    return elegido if _ORDEN_RIESGO.get(elegido, 0) >= _ORDEN_RIESGO.get(sugerido, 0) else sugerido


class ComponenteMaquinaForm(forms.ModelForm):
    class Meta:
        model = ComponenteMaquina
        fields = [
            "id_maquina", "nombre_componente", "tipo_componente", "descripcion",
            "vida_util_estimada_horas", "criticidad_componente",
            "requiere_lubricacion", "requiere_calibracion", "estado_componente",
        ]
        widgets = {
            "id_maquina": forms.Select(attrs=BOOTSTRAP_SELECT),
            "nombre_componente": forms.TextInput(attrs=BOOTSTRAP_INPUT),
            "tipo_componente": forms.Select(attrs=BOOTSTRAP_SELECT),
            "descripcion": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 2}),
            "vida_util_estimada_horas": forms.NumberInput(attrs=BOOTSTRAP_INPUT),
            "criticidad_componente": forms.Select(attrs=BOOTSTRAP_SELECT),
            "requiere_lubricacion": forms.CheckboxInput(attrs=BOOTSTRAP_CHECK),
            "requiere_calibracion": forms.CheckboxInput(attrs=BOOTSTRAP_CHECK),
            "estado_componente": forms.Select(attrs=BOOTSTRAP_SELECT),
        }

    def __init__(self, *args, maquina=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_maquina"].queryset = Maquina.objects.all()
        if maquina is not None:
            self.fields["id_maquina"].initial = maquina
            self.fields["id_maquina"].disabled = True
            self.fields["id_maquina"].widget = forms.HiddenInput()


class FallaProbableForm(forms.ModelForm):
    class Meta:
        model = FallaProbable
        fields = [
            "id_maquina", "id_componente", "descripcion_falla", "causa_probable",
            "efecto_en_produccion", "probabilidad_porcentaje", "nivel_probabilidad",
            "severidad", "detectabilidad", "nivel_riesgo",
            "accion_preventiva_sugerida", "estado",
        ]
        widgets = {
            "id_maquina": forms.Select(attrs=BOOTSTRAP_SELECT),
            "id_componente": forms.Select(attrs=BOOTSTRAP_SELECT),
            "descripcion_falla": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 2}),
            "causa_probable": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 2}),
            "efecto_en_produccion": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 2}),
            "probabilidad_porcentaje": forms.NumberInput(attrs={**BOOTSTRAP_INPUT, "min": 0, "max": 100}),
            "nivel_probabilidad": forms.Select(attrs=BOOTSTRAP_SELECT),
            "severidad": forms.NumberInput(attrs={**BOOTSTRAP_INPUT, "min": 1, "max": 10}),
            "detectabilidad": forms.NumberInput(attrs={**BOOTSTRAP_INPUT, "min": 1, "max": 10}),
            "nivel_riesgo": forms.Select(attrs=BOOTSTRAP_SELECT),
            "accion_preventiva_sugerida": forms.Textarea(attrs={**BOOTSTRAP_INPUT, "rows": 2}),
            "estado": forms.Select(attrs=BOOTSTRAP_SELECT),
        }

    def __init__(self, *args, maquina=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_componente"].required = False
        self.fields["nivel_riesgo"].required = False
        self.fields["nivel_riesgo"].help_text = (
            "Si lo dejas vacío, el sistema lo calcula automáticamente a partir de "
            "la probabilidad, severidad y detectabilidad."
        )
        if maquina is not None:
            self.fields["id_maquina"].initial = maquina
            self.fields["id_maquina"].disabled = True
            self.fields["id_maquina"].widget = forms.HiddenInput()
            self.fields["id_componente"].queryset = ComponenteMaquina.objects.filter(
                id_maquina=maquina
            )
        else:
            self.fields["id_maquina"].queryset = Maquina.objects.all()
            self.fields["id_componente"].queryset = ComponenteMaquina.objects.select_related(
                "id_maquina"
            )

    def clean_severidad(self):
        v = self.cleaned_data.get("severidad")
        if v is not None and not (1 <= v <= 10):
            raise forms.ValidationError("La severidad debe estar entre 1 y 10.")
        return v

    def clean_detectabilidad(self):
        v = self.cleaned_data.get("detectabilidad")
        if v is not None and not (1 <= v <= 10):
            raise forms.ValidationError("La detectabilidad debe estar entre 1 y 10.")
        return v
