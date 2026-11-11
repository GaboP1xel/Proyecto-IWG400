import ast
import json
import re
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase
from django.test.client import RequestFactory
from django.http import HttpResponse

from apps.mapa.agua import calcular_promedios_ph, normalizar_region, obtener_resumen_ph
from apps.mapa.views import mapa_view
from apps.recopilacion.extraccion import _medicion_sinca
from apps.servicio.views import mediciones_api


class PromediosPhTests(SimpleTestCase):
    def test_promedia_solo_valores_numericos_con_region(self):
        resumen = calcular_promedios_ph([
            {"region": "Región A", "valor_promedio": "7,1"},
            {"region": "Región A", "valor_promedio": "8.3"},
            {"region": "Región A", "valor_promedio": ""},
            {"region": "Región A", "valor_promedio": "<7"},
            {"region": None, "valor_promedio": "7.5"},
        ])

        self.assertEqual(resumen["regions"]["Región A"]["average"], "7.70")
        self.assertEqual(resumen["regions"]["Región A"]["service_count"], 2)
        self.assertEqual(resumen["services_with_ph"], 3)
        self.assertEqual(resumen["services_with_region"], 2)
        self.assertEqual(resumen["services_without_region"], 1)

    def test_snapshot_local_tiene_fuente_periodo_y_cobertura(self):
        resumen = obtener_resumen_ph()

        self.assertIn("articles-23695_recurso_202606.xlsx", resumen["source_url"])
        self.assertEqual(resumen["period"], "Junio de 2026")
        self.assertEqual(resumen["services_in_source"], 400)
        self.assertEqual(resumen["services_with_ph"], 176)
        self.assertEqual(
            resumen["services_with_region"] + resumen["services_without_region"],
            resumen["services_with_ph"],
        )
        self.assertTrue(resumen["regions"])


class RegionEstacionTests(SimpleTestCase):
    def test_normaliza_variantes_de_sinca_al_nombre_del_snapshot(self):
        self.assertEqual(
            normalizar_region("Región Aysén del General Carlos Ibáñez del Campo"),
            "Región de Aysén del General Carlos Ibáñez del Campo",
        )
        self.assertEqual(
            normalizar_region("Región de Magallanes y Antártica Chilena"),
            "Región de Magallanes y de la Antártica Chilena",
        )
        self.assertEqual(
            normalizar_region("REGIÓN DE LOS LAGOS"),
            "Región de Los Lagos",
        )

    def test_normaliza_region_interna_de_sinca(self):
        region = "Región de Tarapacá"
        medicion = _medicion_sinca(
            {
                "nombre": "Estación de prueba",
                "latitud": "-20.2",
                "longitud": "-70.1",
                "region": region,
            },
            {
                "tableRow": {
                    "parameter": "MP 2,5",
                    "value": "12.5",
                    "unit": "ug/m3",
                    "datetime": "2026-11-11 10:00",
                }
            },
        )

        self.assertEqual(medicion["region"], region)

    def test_mapa_entrega_region_y_promedio_regional(self):
        medicion = {
            "estacion": "Estación de prueba",
            "parametro": "MP 2,5",
            "valor": Decimal("12.5"),
            "unidad": "ug/m3",
            "fecha": datetime(2026, 11, 11, 10, 0),
            "lat": -20.2,
            "lon": -70.1,
            "region": "Región de Tarapacá",
        }
        resumen = {
            "regions": {
                "Región de Tarapacá": {"average": "7.10", "service_count": 1}
            },
            "services_with_region": 1,
            "services_with_ph": 1,
            "services_without_region": 0,
            "source": "SISS",
            "period": "Junio de 2026",
        }

        with patch(
            "apps.mapa.views.extraer_mediciones_nacional",
            return_value=[medicion],
        ), patch(
            "apps.mapa.views.obtener_resumen_ph",
            return_value=resumen,
        ), patch(
            "apps.mapa.views.render",
            return_value=HttpResponse(),
        ) as render:
            response = mapa_view(RequestFactory().get("/"))

        self.assertEqual(response.status_code, 200)
        contexto = render.call_args.args[2]
        estaciones = json.loads(contexto["estaciones_json"])
        self.assertEqual(estaciones[0]["region"], "Región de Tarapacá")
        self.assertEqual(
            json.loads(contexto["agua_ph_json"])["regions"][
                "Región de Tarapacá"
            ]["average"],
            "7.10",
        )

    def test_template_incluye_json_ph_valido(self):
        resumen = {
            "regions": {"Región de Tarapacá": {"average": "7.10", "service_count": 1}},
            "services_with_region": 1,
            "services_with_ph": 1,
            "services_without_region": 0,
            "source": "SISS",
            "period": "Junio de 2026",
        }

        with patch(
            "apps.mapa.views.extraer_mediciones_nacional",
            return_value=[],
        ), patch("apps.mapa.views.obtener_resumen_ph", return_value=resumen):
            response = self.client.get("/")

        contenido = response.content.decode("utf-8")
        coincidencia = re.search(
            r"const aguaPhData = JSON\.parse\('((?:\\.|[^'])*)'\);",
            contenido,
        )
        self.assertIsNotNone(coincidencia)
        json_escapado = ast.literal_eval("'" + coincidencia.group(1) + "'")
        self.assertEqual(
            json.loads(json_escapado)["regions"]["Región de Tarapacá"]["average"],
            "7.10",
        )

    def test_api_sinca_no_expone_metadato_interno_region(self):
        medicion = {
            "fuente": "SINCA",
            "estacion": "Estación de prueba",
            "region": "Región de Tarapacá",
            "parametro": "MP 2,5",
            "valor": Decimal("12.5"),
            "unidad": "ug/m3",
            "fecha": datetime(2026, 11, 11, 10, 0),
            "lat": -20.2,
            "lon": -70.1,
        }

        with patch(
            "apps.servicio.views.extraer_mediciones_nacional",
            return_value=[medicion],
        ):
            response = mediciones_api(
                RequestFactory().get("/servicio/api/mediciones/sinca/"),
                "sinca",
            )

        item = json.loads(response.content)[0]
        self.assertNotIn("region", item)
        self.assertEqual(
            set(item),
            {
                "fuente", "estacion", "parametro", "valor", "unidad",
                "fecha", "lat", "lon",
            },
        )
