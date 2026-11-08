from datetime import datetime
import csv
import html
import io
import json
import logging
import math
import random
import re
import time
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Optional

import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

URL_SINCA_API = "https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/"


class ErrorExtraccion(Exception):
    """Error al consultar SINCA o interpretar su respuesta."""


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

TIMEOUT = (10, 30)            # (conexión, lectura) en segundos
DELAY_MIN, DELAY_MAX = 3.0, 7.0  # pausa aleatoria entre peticiones
MAX_REINTENTOS = 3
BACKOFF_BASE = 5              # segundos; crece exponencialmente

COLUMNAS = {
    "estacion": "Estacion",
    "parametro": "Parametro",
    "valor": "Valor",
    "unidad": "Unidad",
    "fecha": "Fecha",
    "lat": "Latitud",
    "lon": "Longitud",
}

FORMATOS_FECHA = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%Y-%m-%dT%H:%M:%S")
VALORES_NULOS = {"", "nan", "null", "none", "n/a", "na", "s/d", "-", "--", "-9999", "-999"}

LAT_RANGO = (-56.0, -17.0)
LON_RANGO = (-76.0, -66.0)


@dataclass(frozen=True)
class Medicion:
    fuente: str
    estacion: str
    parametro: str
    valor: Decimal
    unidad: str
    fecha: datetime
    lat: float
    lon: float

    def as_dict(self) -> dict:
        return asdict(self)


def _headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/csv,text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
        "Referer": "https://sinca.mma.gob.cl/",
        "Connection": "keep-alive",
    }


def _pausa() -> None:
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


def descargar(url: str, session: Optional[requests.Session] = None) -> str:
    """Descarga una URL con reintentos y falla explícitamente si no puede obtenerla."""
    sesion = session or requests.Session()
    ultimo_error = None
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            resp = sesion.get(url, headers=_headers(), timeout=TIMEOUT)
            if resp.status_code in (429, 503):
                raise RequestException(f"Limitado por el servidor (HTTP {resp.status_code})")
            resp.raise_for_status()
            try:
                return resp.content.decode("utf-8")
            except UnicodeDecodeError:
                return resp.content.decode("latin-1")
        except Timeout as exc:
            ultimo_error = exc
            logger.warning("Timeout en %s (intento %d/%d)", url, intento, MAX_REINTENTOS)
        except RequestException as exc:
            ultimo_error = exc
            logger.warning("Error de conexión en %s (intento %d/%d): %s", url, intento, MAX_REINTENTOS, exc)

        if intento < MAX_REINTENTOS:
            time.sleep(BACKOFF_BASE * (2 ** (intento - 1)))

    logger.error("Descarga abandonada tras %d intentos: %s", MAX_REINTENTOS, url)
    raise ErrorExtraccion(
        f"No fue posible conectar con SINCA después de {MAX_REINTENTOS} intentos."
    ) from ultimo_error


def _texto(valor) -> Optional[str]:
    if valor is None:
        return None
    limpio = str(valor).strip()
    return None if limpio.lower() in VALORES_NULOS else limpio


def _decimal(valor, permitir_negativo: bool = False) -> Optional[Decimal]:
    texto = _texto(valor)
    if texto is None:
        return None
    try:
        numero = Decimal(texto.replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    if not numero.is_finite():
        return None
    if not permitir_negativo and numero < 0:
        return None
    return numero


def _float_en_rango(valor, rango: tuple) -> Optional[float]:
    numero = _decimal(valor, permitir_negativo=True)
    if numero is None:
        return None
    flotante = float(numero)
    if math.isnan(flotante) or not (rango[0] <= flotante <= rango[1]):
        return None
    return flotante


def _fecha(valor) -> Optional[datetime]:
    texto = _texto(valor)
    if texto is None:
        return None
    for formato in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def validar_fila(fila: dict, fuente: str) -> Optional[Medicion]:
    """Devuelve una Medicion limpia o None si la fila está vacía, nula o corrupta."""
    try:
        estacion = _texto(fila.get(COLUMNAS["estacion"]))
        parametro = _texto(fila.get(COLUMNAS["parametro"]))
        valor = _decimal(fila.get(COLUMNAS["valor"]))
        unidad = _texto(fila.get(COLUMNAS["unidad"])) or ""
        fecha = _fecha(fila.get(COLUMNAS["fecha"]))
        lat = _float_en_rango(fila.get(COLUMNAS["lat"]), LAT_RANGO)
        lon = _float_en_rango(fila.get(COLUMNAS["lon"]), LON_RANGO)
    except (AttributeError, TypeError):
        return None

    if not all([estacion, parametro, valor is not None, fecha, lat is not None, lon is not None]):
        return None

    return Medicion(
        fuente=fuente, estacion=estacion, parametro=parametro,
        valor=valor, unidad=unidad, fecha=fecha, lat=lat, lon=lon,
    )


def extraer_mediciones(url: str, fuente: str) -> list[dict]:
    """Punto de entrada modular: descarga, valida y devuelve solo registros limpios."""
    with requests.Session() as sesion:
        contenido = descargar(url, sesion)
        _pausa()

    lector = csv.DictReader(io.StringIO(contenido))
    if not lector.fieldnames or not set(COLUMNAS.values()).issubset(lector.fieldnames):
        raise ErrorExtraccion(
            "La respuesta CSV de SINCA no contiene las columnas esperadas."
        )

    limpias, descartadas = [], 0

    for fila in lector:
        medicion = validar_fila(fila, fuente)
        if medicion is None:
            descartadas += 1
            continue
        limpias.append(medicion.as_dict())

    logger.info("%s: %d válidas, %d descartadas", fuente, len(limpias), descartadas)
    return limpias


def _unidad(texto) -> str:
    """Convierte entidades HTML de las unidades SINCA a texto legible."""
    sin_etiquetas = re.sub(r"<[^>]*>", "", str(texto or ""))
    return html.unescape(sin_etiquetas).strip()


def _medicion_sinca(estacion: dict, dato: dict) -> Optional[dict]:
    fila = dato.get("tableRow")
    if not isinstance(fila, dict):
        raise ErrorExtraccion("La respuesta JSON de SINCA cambió: falta tableRow.")
    if not fila:
        return None

    requeridos = ("parameter", "value", "unit", "datetime")
    if any(campo not in fila for campo in requeridos):
        raise ErrorExtraccion(
            "La respuesta JSON de SINCA cambió: faltan campos de una medición."
        )

    fecha = _fecha(fila["datetime"])
    valor = _decimal(fila["value"])
    lat = _float_en_rango(estacion.get("latitud"), LAT_RANGO)
    lon = _float_en_rango(estacion.get("longitud"), LON_RANGO)
    nombre = _texto(estacion.get("nombre"))
    parametro = _texto(fila["parameter"])
    if not all((nombre, parametro, valor is not None, fecha, lat is not None, lon is not None)):
        return None

    return {
        "fuente": "SINCA",
        "estacion": nombre,
        "parametro": parametro,
        "valor": valor,
        "unidad": _unidad(fila["unit"]),
        "fecha": fecha,
        "lat": lat,
        "lon": lon,
    }


def extraer_mediciones_nacional(url: str = URL_SINCA_API) -> list[dict]:
    """Consulta el JSON usado por el mapa de SINCA y normaliza sus mediciones recientes."""
    with requests.Session() as sesion:
        contenido = descargar(url, sesion)
        _pausa()

    try:
        estaciones = json.loads(contenido)
    except json.JSONDecodeError as exc:
        raise ErrorExtraccion("SINCA respondió con JSON inválido.") from exc

    if not isinstance(estaciones, list):
        raise ErrorExtraccion("La respuesta JSON de SINCA no tiene el formato esperado.")

    mediciones = []
    for estacion in estaciones:
        if not isinstance(estacion, dict):
            raise ErrorExtraccion("La respuesta JSON de SINCA contiene una estación inválida.")
        if not all(campo in estacion for campo in ("nombre", "latitud", "longitud", "realtime")):
            raise ErrorExtraccion(
                "La respuesta JSON de SINCA cambió: faltan campos de una estación."
            )
        if not isinstance(estacion["realtime"], list):
            raise ErrorExtraccion(
                "La respuesta JSON de SINCA cambió: realtime no es una lista."
            )

        for dato in estacion["realtime"]:
            if not isinstance(dato, dict):
                raise ErrorExtraccion("La respuesta JSON de SINCA contiene una medición inválida.")
            medicion = _medicion_sinca(estacion, dato)
            if medicion is not None:
                mediciones.append(medicion)

    logger.info("SINCA: %d mediciones válidas", len(mediciones))
    return mediciones


if __name__ == "__main__":
    from unittest.mock import patch

    csv_prueba = """Estacion,Parametro,Valor,Unidad,Fecha,Latitud,Longitud
Cerrillos,MP25,12.5,ug/m3,2026-03-29 10:00:00,-33.50,-70.70
Bosquemar,MP25,nan,ug/m3,2026-03-29 10:00:00,-33.50,-70.70
Pudahuel,MP10,45.1,ug/m3,2026-03-29 10:00:00,-33.45,-70.75
Corrupta,CO,s/d,ppm,2026-03-29 10:00:00,-33.45,-70.75
FueraDeChile,SO2,5.0,ppb,2026-03-29 10:00:00,10.0,20.0
"""

    print("Iniciando prueba local de limpieza de datos...")
    with patch("__main__.descargar", return_value=csv_prueba):
        resultados = extraer_mediciones("https://sinca.mma.gob.cl/", "SINCA")
        print(f"\nRegistros procesados con éxito: {len(resultados)} (de 5 ingresados)")
        print("\nDatos limpios listos para guardar o enviar a la API:")
        for r in resultados:
            print(" ->", r)