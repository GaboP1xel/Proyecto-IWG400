from django import forms
from .models import ReporteBasura


class ReporteBasuraForm(forms.ModelForm):
    class Meta:
        model = ReporteBasura
        fields = ['ubicacion', 'descripcion', 'lat', 'lon']
        widgets = {
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Av. Vicuna Mackenna 3939'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el tipo de residuo o microbasural'
            }),
            'lat': forms.HiddenInput(),
            'lon': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('lat')
        lon = cleaned_data.get('lon')

        if lat is None or lon is None:
            raise forms.ValidationError(
                "Debes seleccionar un punto valido en el mapa para registrar las coordenadas."
            )
        return cleaned_data