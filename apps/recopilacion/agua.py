import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import re
import unicodedata


SNAPSHOT_PH = Path(__file__).with_name("data") / "siss_ph_202606.json"
REGIONES_CANONICAS = (
    "Región de Arica y Parinacota",
    "Región de Tarapacá",
    "Región de Antofagasta",
    "Región de Atacama",
    "Región de Coquimbo",
    "Región de Valparaíso",
    "Región Metropolitana de Santiago",
    "Región del Libertador General Bernardo O'Higgins",
    "Región del Maule",
    "Región de Ñuble",
    "Región del Biobío",
    "Región de La Araucanía",
    "Región de Los Ríos",
    "Región de Los Lagos",
    "Región de Aysén del General Carlos Ibáñez del Campo",
    "Región de Magallanes y de la Antártica Chilena",
)


def _clave_region(region):
    sin_acentos = unicodedata.normalize("NFKD", str(region))
    sin_acentos = "".join(
        caracter for caracter in sin_acentos
        if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", sin_acentos.casefold()).strip()


def normalizar_region(region):
    if not region:
        return None

    alias = {
        _clave_region("Región Aysén del General Carlos Ibáñez del Campo"):
            "Región de Aysén del General Carlos Ibáñez del Campo",
        _clave_region("Región de Magallanes y Antártica Chilena"):
            "Región de Magallanes y de la Antártica Chilena",
    }
    canonicas = {_clave_region(nombre): nombre for nombre in REGIONES_CANONICAS}
    clave = _clave_region(region)
    return alias.get(clave, canonicas.get(clave, str(region).strip()))


def _valor_ph(valor):
    if valor is None:
        return None
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
    except InvalidOperation:
        return None
    return numero if numero.is_finite() else None


def calcular_promedios_ph(registros):
    sumas = defaultdict(Decimal)
    cantidades = defaultdict(int)
    servicios_con_ph = 0
    servicios_sin_region = 0

    for registro in registros:
        valor = _valor_ph(registro.get("valor_promedio"))
        if valor is None:
            continue

        servicios_con_ph += 1
        region = registro.get("region")
        if not region:
            servicios_sin_region += 1
            continue

        sumas[region] += valor
        cantidades[region] += 1

    regiones = {
        region: {
            "average": str(
                (sumas[region] / cantidad).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            ),
            "service_count": cantidad,
        }
        for region, cantidad in cantidades.items()
    }

    return {
        "regions": regiones,
        "services_with_ph": servicios_con_ph,
        "services_with_region": servicios_con_ph - servicios_sin_region,
        "services_without_region": servicios_sin_region,
    }


def obtener_resumen_ph():
    with SNAPSHOT_PH.open(encoding="utf-8") as archivo:
        snapshot = json.load(archivo)

    resumen = calcular_promedios_ph(snapshot["records"])
    resumen.update({
        "source": snapshot["source"],
        "source_page": snapshot["source_page"],
        "source_url": snapshot["source_url"],
        "period": snapshot["period"],
        "source_note": snapshot["source_note"],
        "services_in_source": len(snapshot["records"]),
    })
    return resumen
