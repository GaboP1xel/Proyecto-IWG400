import json
from django.test import TestCase
from django.urls import reverse
from .models import ReporteBasura
from .forms import ReporteBasuraForm


class ReporteBasuraTests(TestCase):
    def test_creacion_modelo_reporte(self):
        reporte = ReporteBasura.objects.create(
            ubicacion="Parque San Borja",
            descripcion="Escombros en la esquina norte",
            lat=-33.4429,
            lon=-70.6358
        )
        self.assertEqual(reporte.estado, 'pendiente')
        self.assertEqual(str(reporte), "Reporte en Parque San Borja (Pendiente)")

    def test_formulario_rechaza_reporte_sin_coordenadas(self):
        form = ReporteBasuraForm(data={
            'ubicacion': 'Plaza de Armas',
            'descripcion': 'Basura acumulada'
        })
        self.assertFalse(form.is_valid())

    def test_vista_registrar_reporte_json(self):
        url = reverse('reportes:registrar_reporte')
        payload = {
            'ubicacion': 'Campus San Joaquin',
            'descripcion': 'Contenedor lleno',
            'lat': -33.4904,
            'lon': -70.6190
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ReporteBasura.objects.count(), 1)