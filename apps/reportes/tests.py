import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ReporteCiudadano, TipoReporte

User = get_user_model()


class ReportesBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="vecino_test", password="password123")
        self.tipo = TipoReporte.objects.create(
            nombre="Microbasural", descripcion="Acumulación de basura en vía pública"
        )
        self.url_crear = reverse("reportes:crear_reporte")
        self.url_listar = reverse("reportes:listar_reportes_api")

    def test_crear_reporte_json_exitoso(self):
        self.client.login(username="vecino_test", password="password123")
        payload = {
            "tipo_reporte": self.tipo.id,
            "descripcion": "Basura acumulada en la esquina de la plaza principal.",
            "lat": -33.4378,
            "lon": -70.6504,
        }
        response = self.client.post(
            self.url_crear,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ReporteCiudadano.objects.count(), 1)
        reporte = ReporteCiudadano.objects.first()
        self.assertEqual(reporte.usuario, self.user)
        self.assertEqual(reporte.estado, "pendiente")

    def test_rechaza_coordenadas_invalidas(self):
        self.client.login(username="vecino_test", password="password123")
        payload = {
            "tipo_reporte": self.tipo.id,
            "descripcion": "Coordenadas fuera del planeta Tierra.",
            "lat": -150.0,
            "lon": -70.6504,
        }
        response = self.client.post(
            self.url_crear,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ReporteCiudadano.objects.count(), 0)

    def test_listar_reportes_api(self):
        ReporteCiudadano.objects.create(
            usuario=self.user,
            tipo_reporte=self.tipo,
            descripcion="Reporte de prueba visible en mapa",
            lat=-33.4378,
            lon=-70.6504,
        )
        response = self.client.get(self.url_listar)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["reportes"]), 1)