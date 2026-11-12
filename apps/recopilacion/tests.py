import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import Client, SimpleTestCase
from requests.exceptions import ConnectionError, HTTPError, Timeout

from apps.recopilacion.agua import (
    calcular_promedios_ph,
    normalizar_region,
    obtener_resumen_ph,
)
from apps.recopilacion.extraccion import (
    BACKOFF_BASE,
    ErrorExtraccion,
    descargar,
    extraer_mediciones_nacional,
)


def estacion(realtime=None, **campos):
    datos = {
        "nombre": "Estación de prueba",
        "latitud": -33.45,
        "longitud": -70.66,
        "realtime": realtime if realtime is not None else [{
            "tableRow": {
                "parameter": "MP25",
                "value": "12.5",
                "unit": "ug/m3",
                "datetime": "2026-11-08 10:00:00",
            },
        }],
    }
    datos.update(campos)
    return datos


class ResumenAguaPHTests(SimpleTestCase):
    def test_promedia_valores_numericos_por_region(self):
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

    def test_normaliza_variantes_de_nombres_regionales(self):
        self.assertEqual(
            normalizar_region("Región Aysén del General Carlos Ibáñez del Campo"),
            "Región de Aysén del General Carlos Ibáñez del Campo",
        )
        self.assertEqual(
            normalizar_region("Región de Magallanes y Antártica Chilena"),
            "Región de Magallanes y de la Antártica Chilena",
        )
        self.assertEqual(normalizar_region("REGIÓN DE LOS LAGOS"), "Región de Los Lagos")

    def test_snapshot_siss_entrega_resumen_y_cobertura(self):
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


class ExtraerMedicionesNacionalTests(SimpleTestCase):
    @patch("apps.recopilacion.extraccion._pausa")
    @patch("apps.recopilacion.extraccion.descargar")
    def test_extrae_medicion_y_no_aplica_pausa_csv(self, mock_descargar, mock_pausa):
        mock_descargar.return_value = json.dumps([estacion()])

        resultado = extraer_mediciones_nacional()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            set(resultado[0]),
            {"fuente", "estacion", "parametro", "valor", "unidad", "fecha", "lat", "lon"},
        )
        self.assertEqual(resultado[0]["fuente"], "SINCA")
        self.assertEqual(resultado[0]["valor"], Decimal("12.5"))
        self.assertEqual(resultado[0]["fecha"], datetime(2026, 11, 8, 10, 0))
        mock_pausa.assert_not_called()

    @patch("apps.recopilacion.extraccion.descargar", return_value="[]")
    def test_respuesta_json_vacia_devuelve_lista_vacia(self, _mock_descargar):
        self.assertEqual(extraer_mediciones_nacional(), [])

    @patch("apps.recopilacion.extraccion.descargar")
    def test_estacion_sin_realtime_no_impide_extraer_las_demas(self, mock_descargar):
        mock_descargar.return_value = json.dumps([
            {"nombre": "Sin realtime", "latitud": -33.45, "longitud": -70.66},
            estacion(),
        ])

        resultado = extraer_mediciones_nacional()

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["estacion"], "Estación de prueba")

    @patch("apps.recopilacion.extraccion.descargar")
    def test_fecha_no_reconocida_no_se_reporta_como_respuesta_vacia(self, mock_descargar):
        mock_descargar.return_value = json.dumps([estacion(realtime=[{
            "tableRow": {
                "parameter": "MP25",
                "value": "12.5",
                "unit": "ug/m3",
                "datetime": "08/11/2026 10:00",
            },
        }])])

        with self.assertRaisesRegex(ErrorExtraccion, "ninguna pudo interpretarse"):
            extraer_mediciones_nacional()

    @patch("apps.recopilacion.extraccion.descargar")
    def test_unidad_decodifica_entidades_html(self, mock_descargar):
        mock_descargar.return_value = json.dumps([estacion(realtime=[{
            "tableRow": {
                "parameter": "MP25",
                "value": "12.5",
                "unit": "&micro;g/m<sup>3</sup>",
                "datetime": "2026-11-08 10:00:00",
            },
        }])])

        resultado = extraer_mediciones_nacional()

        self.assertEqual(resultado[0]["unidad"], "µg/m3")


class DescargarTests(SimpleTestCase):
    @patch("apps.recopilacion.extraccion.time.sleep")
    @patch("apps.recopilacion.extraccion._headers", return_value={})
    def test_error_http_404_no_se_reintenta(self, _mock_headers, mock_sleep):
        session = Mock()
        respuesta = Mock(status_code=404)
        respuesta.raise_for_status.side_effect = HTTPError("404 Client Error")
        session.get.return_value = respuesta

        with self.assertRaisesRegex(ErrorExtraccion, "HTTP 404"):
            descargar("https://sinca.test/datos", session)

        session.get.assert_called_once()
        mock_sleep.assert_not_called()

    @patch("apps.recopilacion.extraccion.time.sleep")
    @patch("apps.recopilacion.extraccion._headers", return_value={})
    def test_http_transitorios_se_reintentan_y_luego_se_recuperan(
        self, _mock_headers, mock_sleep
    ):
        for status in (429, 500, 503, 599):
            with self.subTest(status=status):
                session = Mock()
                session.get.side_effect = [
                    Mock(status_code=status),
                    Mock(status_code=200, content=b"[]"),
                ]

                self.assertEqual(descargar("https://sinca.test/datos", session), "[]")

                self.assertEqual(session.get.call_count, 2)
                mock_sleep.assert_called_once_with(BACKOFF_BASE)
                mock_sleep.reset_mock()

    @patch("apps.recopilacion.extraccion.time.sleep")
    @patch("apps.recopilacion.extraccion._headers", return_value={})
    def test_errores_de_conexion_y_timeout_se_reintentan(
        self, _mock_headers, mock_sleep
    ):
        for error in (ConnectionError("connection failed"), Timeout("timed out")):
            with self.subTest(error=type(error).__name__):
                session = Mock()
                session.get.side_effect = [
                    error,
                    Mock(status_code=200, content=b"[]"),
                ]

                self.assertEqual(descargar("https://sinca.test/datos", session), "[]")

                self.assertEqual(session.get.call_count, 2)
                mock_sleep.assert_called_once_with(BACKOFF_BASE)
                mock_sleep.reset_mock()


class MedicionesAPITests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch("apps.recopilacion.views.extraer_mediciones_nacional")
    def test_api_200_contrato_de_ocho_claves(self, mock_extraer):
        mock_extraer.return_value = [{
            "fuente": "SINCA",
            "estacion": "Estación de prueba",
            "parametro": "MP25",
            "valor": Decimal("12.5"),
            "unidad": "µg/m3",
            "fecha": datetime(2026, 11, 8, 10, 0),
            "lat": -33.45,
            "lon": -70.66,
        }]

        respuesta = self.client.get("/servicio/api/mediciones/sinca/")

        self.assertEqual(respuesta.status_code, 200)
        medicion = respuesta.json()[0]
        self.assertEqual(
            set(medicion),
            {"fuente", "estacion", "parametro", "valor", "unidad", "fecha", "lat", "lon"},
        )
        self.assertEqual(medicion["valor"], "12.5")
        self.assertEqual(medicion["fecha"], "2026-11-08T10:00:00")

    @patch("apps.recopilacion.views.extraer_mediciones_nacional")
    def test_fuente_desconocida_devuelve_404(self, mock_extraer):
        respuesta = self.client.get("/servicio/api/mediciones/desconocida/")

        self.assertEqual(respuesta.status_code, 404)
        mock_extraer.assert_not_called()

    @patch(
        "apps.recopilacion.views.extraer_mediciones_nacional",
        side_effect=ErrorExtraccion("SINCA no responde."),
    )
    def test_error_de_extraccion_devuelve_502(self, _mock_extraer):
        respuesta = self.client.get("/servicio/api/mediciones/sinca/")

        self.assertEqual(respuesta.status_code, 502)
        self.assertEqual(respuesta.json(), {"error": "SINCA no responde."})
