from django import forms
from .models import ReporteCiudadano


class ReporteCiudadanoForm(forms.ModelForm):
    class Meta:
        model = ReporteCiudadano
        # Solo exponemos los campos que el ciudadano debe enviar.
        # 'usuario' y 'estado' los asigna el backend automáticamente por seguridad.
        fields = ["tipo_reporte", "descripcion", "lat", "lon"]
        widgets = {
            "tipo_reporte": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe el problema ambiental o microbasural...",
                }
            ),
            "lat": forms.HiddenInput(),
            "lon": forms.HiddenInput(),
        }

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get("descripcion", "").strip()
        if len(descripcion) < 10:
            raise forms.ValidationError(
                "La descripción es muy corta. Por favor detalla un poco más el reporte (mínimo 10 caracteres)."
            )
        return descripcion

    def clean_lat(self):
        lat = self.cleaned_data.get("lat")
        if lat is None:
            raise forms.ValidationError("Debes seleccionar una ubicación en el mapa (latitud faltante).")
        if not (-90.0 <= lat <= 90.0):
            raise forms.ValidationError("La latitud ingresada no es válida (debe estar entre -90 y 90).")
        return lat

    def clean_lon(self):
        lon = self.cleaned_data.get("lon")
        if lon is None:
            raise forms.ValidationError("Debes seleccionar una ubicación en el mapa (longitud faltante).")
        if not (-180.0 <= lon <= 180.0):
            raise forms.ValidationError("La longitud ingresada no es válida (debe estar entre -180 y 180).")
        return lon