import json
import logging
import re
import unicodedata
from collections import defaultdict
from django.conf import settings
from recopilacion.extraccion import ErrorExtraccion, extraer_mediciones_nacional

logger = logging.getLogger(__name__)

# Cache en memoria para no leer el GeoJSON desde disco en cada recarga
_COMUNAS_POLIGONOS = None


def normalizar_texto(texto: str) -> str:
    """Pasa a mayúsculas, quita tildes y normaliza espacios."""
    if not texto:
        return ""
    sin_tildes = unicodedata.normalize("NFD", str(texto)).encode("ascii", "ignore").decode("utf-8")
    return " ".join(sin_tildes.strip().upper().split())


def normalizar_parametro(parametro: str) -> str:
    """Limpia HTML, espacios y comas para unificar 'MP 2,5' -> 'MP25' y 'MP 10' -> 'MP10'."""
    if not parametro:
        return ""
    limpio = re.sub(r"<[^>]*>", "", str(parametro))
    return (
        limpio.strip()
        .upper()
        .replace(" ", "")
        .replace(".", "")
        .replace(",", "")
        .replace("PM", "MP")
    )


def clasificar_mp25(valor: float) -> tuple[str, str]:
    """Clasificación oficial MMA para MP2.5 (µg/m³)."""
    if valor <= 49:
        return "Bueno", "#28a745"          # Verde
    elif valor <= 79:
        return "Regular", "#ffc107"        # Amarillo
    elif valor <= 109:
        return "Alerta", "#fd7e14"         # Naranja
    elif valor <= 169:
        return "Preemergencia", "#dc3545"  # Rojo
    else:
        return "Emergencia", "#6f42c1"     # Morado


def clasificar_mp10(valor: float) -> tuple[str, str]:
    """Clasificación oficial MMA para MP10 (µg/m³) como respaldo."""
    if valor <= 149:
        return "Bueno", "#28a745"
    elif valor <= 194:
        return "Regular", "#ffc107"
    elif valor <= 239:
        return "Alerta", "#fd7e14"
    elif valor <= 329:
        return "Preemergencia", "#dc3545"
    else:
        return "Emergencia", "#6f42c1"


# =========================================================================
# GEOMETRÍA PURA EN PYTHON (Sin dependencias externas)
# =========================================================================
def _punto_en_anillo(lon: float, lat: float, anillo: list) -> bool:
    """Algoritmo Ray Casting para saber si (lon, lat) cae dentro de un anillo."""
    dentro = False
    n = len(anillo)
    if n < 3:
        return False
    p1_lon, p1_lat = anillo[0][0], anillo[0][1]
    for i in range(1, n + 1):
        p2_lon, p2_lat = anillo[i % n][0], anillo[i % n][1]
        if min(p1_lat, p2_lat) < lat <= max(p1_lat, p2_lat):
            if lon <= max(p1_lon, p2_lon):
                if p1_lat != p2_lat:
                    x_interseccion = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                if p1_lon == p2_lon or lon <= x_interseccion:
                    dentro = not dentro
        p1_lon, p1_lat = p2_lon, p2_lat
    return dentro


def _punto_en_poligono(lon: float, lat: float, poligono: list) -> bool:
    """Evalúa anillo exterior (índice 0) y posibles agujeros interiores (índices 1+)."""
    if not poligono or not _punto_en_anillo(lon, lat, poligono[0]):
        return False
    for agujero in poligono[1:]:
        if _punto_en_anillo(lon, lat, agujero):
            return False
    return True


def _cargar_poligonos_comunas() -> list[dict]:
    """Carga y precalcula los bounding boxes de comunas.geojson una sola vez."""
    global _COMUNAS_POLIGONOS
    if _COMUNAS_POLIGONOS is not None:
        return _COMUNAS_POLIGONOS

    ruta_geojson = settings.BASE_DIR / "static" / "geojson" / "comunas.geojson"
    with open(ruta_geojson, encoding="utf-8") as f:
        data = json.load(f)

    poligonos = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry") or {}
        tipo = geom.get("type")
        coords = geom.get("coordinates", [])

        if tipo == "Polygon":
            lista_poligonos = [coords]
        elif tipo == "MultiPolygon":
            lista_poligonos = coords
        else:
            continue

        todos_puntos = [pt for poly in lista_poligonos for anillo in poly for pt in anillo]
        if not todos_puntos:
            continue

        lons = [pt[0] for pt in todos_puntos]
        lats = [pt[1] for pt in todos_puntos]

        poligonos.append({
            "comuna": props.get("Comuna", ""),
            "comuna_norm": normalizar_texto(props.get("Comuna", "")),
            "region": props.get("Region", ""),
            "region_norm": normalizar_texto(props.get("Region", "")),
            "bbox": (min(lons), min(lats), max(lons), max(lats)),
            "poligonos": lista_poligonos,
        })

    _COMUNAS_POLIGONOS = poligonos
    return _COMUNAS_POLIGONOS


def ubicar_comuna_y_region(lat: float, lon: float) -> tuple[str, str, str, str] | None:
    """Devuelve (comuna, comuna_norm, region, region_norm) para una coordenada."""
    for item in _cargar_poligonos_comunas():
        min_lon, min_lat, max_lon, max_lat = item["bbox"]
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            continue
        for poly in item["poligonos"]:
            if _punto_en_poligono(lon, lat, poly):
                return (
                    item["comuna"],
                    item["comuna_norm"],
                    item["region"],
                    item["region_norm"],
                )
    return None


# =========================================================================
# PROCESAMIENTO PRINCIPAL DE DATOS SINCA
# =========================================================================
def obtener_datos_aire_mapa() -> dict:
    """
    Consulta SINCA, ubica cada estación en su comuna/región,
    calcula promedios y clasifica comunas y regiones.
    """
    try:
        mediciones = extraer_mediciones_nacional()
    except ErrorExtraccion as exc:
        logger.warning("No se pudo obtener datos de SINCA: %s", exc)
        return {"comunas": {}, "regiones": {}, "error": str(exc)}

    acum_comunas = defaultdict(lambda: {"mp25": [], "mp10": [], "estaciones": set(), "fecha": ""})
    acum_regiones = defaultdict(lambda: {"mp25": [], "mp10": []})

    for m in mediciones:
        param = normalizar_parametro(m["parametro"])
        if param not in ("MP25", "MP10"):
            continue

        ubicacion = ubicar_comuna_y_region(m["lat"], m["lon"])
        if not ubicacion:
            continue

        _, comuna_norm, _, region_norm = ubicacion
        valor = float(m["valor"])
        fecha_str = m["fecha"].strftime("%d/%m/%Y %H:%M") if m.get("fecha") else ""

        clave_param = "mp25" if param == "MP25" else "mp10"
        acum_comunas[comuna_norm][clave_param].append(valor)
        acum_comunas[comuna_norm]["estaciones"].add(m["estacion"])
        if fecha_str:
            acum_comunas[comuna_norm]["fecha"] = fecha_str

        if region_norm:
            acum_regiones[region_norm][clave_param].append(valor)

    # 1. Consolidar y clasificar por Comuna
    datos_comunas = {}
    for comuna_norm, info in acum_comunas.items():
        if info["mp25"]:
            promedio = round(sum(info["mp25"]) / len(info["mp25"]), 1)
            estado, color = clasificar_mp25(promedio)
            parametro_usado = "MP2.5"
        elif info["mp10"]:
            promedio = round(sum(info["mp10"]) / len(info["mp10"]), 1)
            estado, color = clasificar_mp10(promedio)
            parametro_usado = "MP10"
        else:
            continue

        datos_comunas[comuna_norm] = {
            "valor": promedio,
            "parametro": parametro_usado,
            "unidad": "µg/m³",
            "estado": estado,
            "color": color,
            "estaciones": sorted(info["estaciones"]),
            "fecha": info["fecha"],
        }

    # 2. Consolidar, promediar y clasificar por Región
    datos_regiones = {}
    for region_norm, info in acum_regiones.items():
        if info["mp25"]:
            promedio = round(sum(info["mp25"]) / len(info["mp25"]), 1)
            estado, color = clasificar_mp25(promedio)
            parametro_usado = "MP2.5"
            total_mediciones = len(info["mp25"])
        elif info["mp10"]:
            promedio = round(sum(info["mp10"]) / len(info["mp10"]), 1)
            estado, color = clasificar_mp10(promedio)
            parametro_usado = "MP10"
            total_mediciones = len(info["mp10"])
        else:
            continue

        datos_regiones[region_norm] = {
            "promedio": promedio,
            "parametro": parametro_usado,
            "unidad": "µg/m³",
            "estado": estado,
            "color": color,
            "total_mediciones": total_mediciones,
        }

    return {
        "comunas": datos_comunas,
        "regiones": datos_regiones,
        "error": None,
    }