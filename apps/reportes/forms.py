from django import forms

from apps.core.models import Area, Maquina

INP = {"class": "form-control"}
SEL = {"class": "form-select"}


class ReportePeriodoForm(forms.Form):
    TIPO = [
        ("SEMANAL", "Semanal"), ("DIARIO", "Diario"), ("MENSUAL", "Mensual"),
        ("POR_MAQUINA", "Por máquina"), ("POR_AREA", "Por área"),
        ("PERSONALIZADO", "Personalizado"),
    ]
    tipo_reporte = forms.ChoiceField(
        label="Tipo de reporte", choices=TIPO, widget=forms.Select(attrs=SEL)
    )
    fecha_inicio = forms.DateField(
        label="Fecha de inicio", widget=forms.DateInput(attrs={**INP, "type": "date"})
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin", widget=forms.DateInput(attrs={**INP, "type": "date"})
    )
    id_area = forms.ModelChoiceField(
        label="Área (opcional)", queryset=Area.objects.all(), required=False,
        widget=forms.Select(attrs=SEL),
    )
    id_maquina = forms.ModelChoiceField(
        label="Máquina (opcional)", queryset=Maquina.objects.all(), required=False,
        widget=forms.Select(attrs=SEL),
    )

    def clean(self):
        datos = super().clean()
        ini, fin = datos.get("fecha_inicio"), datos.get("fecha_fin")
        if ini and fin and fin < ini:
            raise forms.ValidationError("La fecha de fin no puede ser anterior a la de inicio.")
        return datos
