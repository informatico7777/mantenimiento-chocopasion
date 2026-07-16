from django import forms
from django.conf import settings

from .models import ArchivoAdjunto

INP = {"class": "form-control"}
SEL = {"class": "form-select"}


class ArchivoAdjuntoForm(forms.Form):
    tipo_entidad = forms.ChoiceField(
        label="Tipo de entidad", choices=ArchivoAdjunto.TIPO_ENTIDAD,
        widget=forms.Select(attrs=SEL),
    )
    id_entidad = forms.IntegerField(
        label="ID de la entidad (máquina, OT, falla, etc.)",
        min_value=1, widget=forms.NumberInput(attrs=INP),
    )
    categoria_archivo = forms.ChoiceField(
        label="Categoría", choices=ArchivoAdjunto.CATEGORIA,
        widget=forms.Select(attrs=SEL),
    )
    descripcion = forms.CharField(
        label="Descripción", required=False,
        widget=forms.Textarea(attrs={**INP, "rows": 2}),
    )
    archivo = forms.FileField(
        label="Archivo",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        nombre = archivo.name.lower()
        ext = nombre.rsplit(".", 1)[-1] if "." in nombre else ""
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise forms.ValidationError(
                "Extensión no permitida. Permitidas: "
                + ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
            )
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if archivo.size > max_bytes:
            raise forms.ValidationError(
                f"El archivo supera el máximo de {settings.MAX_UPLOAD_SIZE_MB} MB."
            )
        return archivo
