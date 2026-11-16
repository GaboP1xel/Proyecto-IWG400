import json
import logging
import unicodedata
from collections import defaultdict
from django.conf import settings

logger = logging.getLogger(__name__)

_CACHE_AGUA = None

# Localidades o sectores que en SISS aparecen con su nombre local en vez de la comuna
ALIAS_SERVICIOS_COMUNA = {
    "RENACA": ["VINA DEL MAR"],
    "CONCON": ["CONCON"],
    "CURAUMA": ["VALPARAISO"],
    "PLACILLA": ["VALPARAISO"],
    "PLACILLA DE PENUELAS": ["VALPARAISO"],
    "LAGUNA VERDE": ["VALPARAISO"],
    "LAS VENTANAS": ["PUCHUNCAVI"],
    "HORCON": ["PUCHUNCAVI"],
    "MAITENCILLO": ["PUCHUNCAVI"],
    "CACHAGUA": ["ZAPALLAR"],
    "LLOLLEO": ["SAN ANTONIO"],
    "TEJAS VERDES": ["SAN ANTONIO"],
    "CARTAGENA": ["CARTAGENA"],
    "EL TABO": ["EL TABO"],
    "LAS CRUCES": ["EL TABO"],
    "EL QUISCO": ["EL QUISCO"],
    "ALGARROBO": ["ALGARROBO"],
    "CHICUREO": ["COLINA"],
    "CHAMISERO": ["COLINA"],
    "BATUCO": ["LAMPA"],
    "VALLE GRANDE": ["LAMPA"],
    "CIUDAD DE LOS VALLES": ["PUDAHUEL"],
    "NOS": ["SAN BERNARDO"],
    "LO HERRERA": ["SAN BERNARDO"],
    "LINDEROS": ["BUIN"],
    "ALTO JAHUEL": ["BUIN"],
    "HOSPITAL": ["PAINE"],
    "CHAMPA": ["PAINE"],
    "MELIPILLA": ["MELIPILLA"],
    "SAN JOSE DE MAIPO": ["SAN JOSE DE MAIPO"],
    "LAS VERTIENTES": ["SAN JOSE DE MAIPO"],
    "EL CANELO": ["SAN JOSE DE MAIPO"],
    "EL MELOCOTON": ["SAN JOSE DE MAIPO"],
    "SAN ALFONSO": ["SAN JOSE DE MAIPO"],
    "SAN GABRIEL": ["SAN JOSE DE MAIPO"],
    "MACHALI": ["MACHALI"],
    "COYA": ["MACHALI"],
    "LO MIRANDA": ["DONIHUE"],
    "ROSARIO": ["RENGO"],
    "PELEQUEN": ["MALLOA"],
    "SAN PEDRO": ["SAN PEDRO DE LA PAZ"],
    "LOMAS COLORADAS": ["SAN PEDRO DE LA PAZ"],
    "CHIGUAYANTE": ["CHIGUAYANTE"],
    "HUALPEN": ["HUALPEN"],
    "LIRQUEN": ["PENCO"],
    "TOME": ["TOME"],
    "DICHATO": ["TOME"],
    "LABRANZA": ["TEMUCO"],
    "CAJON": ["VILCUN"],
    "LICAN RAY": ["VILLARRICA"],
    "NIEBLA": ["VALDIVIA"],
    "RAHUE": ["OSORNO"],
    "ALERCE": ["PUERTO MONTT"],
    "PUERTO VARAS": ["PUERTO VARAS"],
    "LLANQUIHUE": ["LLANQUIHUE"],
    "CHACAO": ["ANCUD"],
    "PUERTO AYSEN": ["AYSEN"],
    "PUERTO CHACABUCO": ["AYSEN"],
}

# Palabras clave únicas para emparejar nombres de regiones entre SISS y el GeoJSON
CLAVES_REGIONES = (
    "ARICA", "TARAPACA", "ANTOFAGASTA", "ATACAMA", "COQUIMBO",
    "VALPARAISO", "METROPOLITANA", "HIGGINS", "MAULE", "NUBLE",
    "BIOBIO", "ARAUCANIA", "RIOS", "LAGOS", "AYSEN", "MAGALLANES",
)


def normalizar_texto(texto: str) -> str:
    """Pasa a mayúsculas, quita tildes y normaliza espacios."""
    if not texto:
        return ""
    sin_tildes = unicodedata.normalize("NFD", str(texto)).encode("ascii", "ignore").decode("utf-8")
    return " ".join(sin_tildes.strip().upper().split())


def clasificar_ph(valor: float) -> tuple[str, str]:
    """Clasifica el pH según la norma chilena de agua potable NCh 409 (6.5 a 8.5)."""
    if 6.5 <= valor <= 8.5:
        return "Óptimo (Cumple NCh 409)", "#28a745"   # Verde
    elif (6.0 <= valor < 6.5) or (8.5 < valor <= 9.0):
        return "Leve desviación", "#ffc107"          # Amarillo
    else:
        return "Fuera de norma NCh 409", "#dc3545"   # Rojo


def _parsear_ph(valor_raw) -> float | None:
    """Convierte '7,3196' o '6.8' a float válido; devuelve None si viene vacío o inválido."""
    if valor_raw is None:
        return None
    texto = str(valor_raw).strip().replace(",", ".")
    if not texto:
        return None
    try:
        numero = float(texto)
        return numero if 0.0 <= numero <= 14.0 else None
    except ValueError:
        return None


def _cargar_catalogo_geojson() -> tuple[dict[str, str], set[str]]:
    """
    Lee comunas.geojson y construye:
    - mapa_comunas: {COMUNA_NORM: REGION_NORM}
    - regiones_validas: {REGION_NORM, ...}
    """
    ruta_geojson = settings.BASE_DIR / "static" / "geojson" / "comunas.geojson"
    with open(ruta_geojson, encoding="utf-8") as f:
        data = json.load(f)

    mapa_comunas = {}
    regiones_validas = set()
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        com_norm = normalizar_texto(props.get("Comuna", ""))
        reg_norm = normalizar_texto(props.get("Region", ""))
        if com_norm:
            mapa_comunas[com_norm] = reg_norm
        if reg_norm:
            regiones_validas.add(reg_norm)

    return mapa_comunas, regiones_validas


def _resolver_region_geojson(region_raw: str, regiones_validas: set[str]) -> str:
    """Empareja el nombre de región de SISS con la clave exacta de regiones.geojson."""
    reg_norm = normalizar_texto(region_raw)
    if not reg_norm:
        return ""
    if reg_norm in regiones_validas:
        return reg_norm

    for clave in CLAVES_REGIONES:
        if clave in reg_norm:
            for reg_geo in regiones_validas:
                if clave in reg_geo:
                    return reg_geo
    return ""


def _resolver_comunas_servicio(servicio: str, mapa_comunas: dict[str, str]) -> list[str]:
    """
    Identifica a qué comuna(s) de comunas.geojson corresponde el 'servicio' de SISS.
    Soporta coincidencias directas, alias locales y servicios compuestos ('MAIPU - CERRILLOS').
    """
    serv_norm = normalizar_texto(servicio)
    if not serv_norm:
        return []

    # 1. Coincidencia directa o por alias completo
    if serv_norm in mapa_comunas:
        return [serv_norm]
    if serv_norm in ALIAS_SERVICIOS_COMUNA:
        return [c for c in ALIAS_SERVICIOS_COMUNA[serv_norm] if c in mapa_comunas]

    # 2. Servicios compuestos separados por guion (ej. "MAIPU - CERRILLOS" o "TEMUCO - CENTRO")
    encontradas = []
    partes = [p.strip() for p in serv_norm.split("-") if p.strip()]
    for parte in partes:
        if parte in mapa_comunas and parte not in encontradas:
            encontradas.append(parte)
        elif parte in ALIAS_SERVICIOS_COMUNA:
            for c in ALIAS_SERVICIOS_COMUNA[parte]:
                if c in mapa_comunas and c not in encontradas:
                    encontradas.append(c)

    return encontradas


def _buscar_ruta_json_siss():
    """Localiza siss_ph_202606.json dentro de la app recopilacion."""
    rutas_posibles = [
        settings.BASE_DIR / "apps" / "recopilacion" / "data" / "siss_ph_202606.json",
        settings.BASE_DIR / "recopilacion" / "data" / "siss_ph_202606.json",
    ]
    for ruta in rutas_posibles:
        if ruta.exists():
            return ruta
    return None


def obtener_datos_agua_mapa() -> dict:
    """
    Procesa siss_ph_202606.json, cruza los servicios con comunas.geojson y
    devuelve los indicadores de calidad de agua potable (pH - NCh 409) por comuna y región.
    """
    global _CACHE_AGUA
    if _CACHE_AGUA is not None:
        return _CACHE_AGUA

    ruta_json = _buscar_ruta_json_siss()
    if not ruta_json:
        msg = "No se encontró el archivo siss_ph_202606.json en recopilacion/data/"
        logger.warning(msg)
        return {"comunas": {}, "regiones": {}, "periodo": "", "error": msg}

    try:
        with open(ruta_json, encoding="utf-8") as f:
            snapshot = json.load(f)
    except Exception as exc:
        logger.exception("Error leyendo siss_ph_202606.json")
        return {"comunas": {}, "regiones": {}, "periodo": "", "error": str(exc)}

    mapa_comunas, regiones_validas = _cargar_catalogo_geojson()
    records = snapshot.get("records", [])
    periodo = snapshot.get("period") or snapshot.get("periodo") or "Junio 2026"

    acum_comunas = defaultdict(lambda: {
        "valores": [],
        "evaluaciones": set(),
        "servicios": set(),
    })
    acum_regiones = defaultdict(lambda: {
        "valores": [],
        "evaluaciones": set(),
        "servicios_count": 0,
    })

    for rec in records:
        servicio = (rec.get("servicio") or "").strip()
        if not servicio:
            continue

        ph_val = _parsear_ph(rec.get("valor_promedio"))
        eval_norm = normalizar_texto(rec.get("evaluacion", ""))

        # Ignorar registros sin dato numérico ni evaluación útil
        if ph_val is None and eval_norm not in ("CUMPLE", "NO CUMPLE"):
            continue

        comunas_asociadas = _resolver_comunas_servicio(servicio, mapa_comunas)
        regiones_del_registro = set()

        for com_norm in comunas_asociadas:
            acum_comunas[com_norm]["servicios"].add(servicio)
            if ph_val is not None:
                acum_comunas[com_norm]["valores"].append(ph_val)
            if eval_norm:
                acum_comunas[com_norm]["evaluaciones"].add(eval_norm)

            reg_comuna = mapa_comunas.get(com_norm, "")
            if reg_comuna:
                regiones_del_registro.add(reg_comuna)

        # Si el registro no cruzó con ninguna comuna, usar la región declarada en el JSON
        if not regiones_del_registro:
            reg_json = _resolver_region_geojson(rec.get("region", ""), regiones_validas)
            if reg_json:
                regiones_del_registro.add(reg_json)

        for reg_norm in regiones_del_registro:
            acum_regiones[reg_norm]["servicios_count"] += 1
            if ph_val is not None:
                acum_regiones[reg_norm]["valores"].append(ph_val)
            if eval_norm:
                acum_regiones[reg_norm]["evaluaciones"].add(eval_norm)

    # 1. Consolidar por Comuna
    datos_comunas = {}
    for com_norm, info in acum_comunas.items():
        servicios_lista = sorted(info["servicios"])
        if info["valores"]:
            promedio = round(sum(info["valores"]) / len(info["valores"]), 2)
            estado, color = clasificar_ph(promedio)
        elif "NO CUMPLE" in info["evaluaciones"]:
            promedio = None
            estado, color = "Fuera de norma NCh 409", "#dc3545"
        elif "CUMPLE" in info["evaluaciones"]:
            promedio = None
            estado, color = "Cumple norma (6,5 - 8,5)", "#28a745"
        else:
            continue

        datos_comunas[com_norm] = {
            "valor": promedio,
            "parametro": "pH",
            "limite": "6,5 - 8,5",
            "estado": estado,
            "color": color,
            "servicios": servicios_lista,
            "periodo": periodo,
        }

    # 2. Consolidar por Región
    datos_regiones = {}
    for reg_norm, info in acum_regiones.items():
        if info["valores"]:
            promedio = round(sum(info["valores"]) / len(info["valores"]), 2)
            estado, color = clasificar_ph(promedio)
        elif "NO CUMPLE" in info["evaluaciones"]:
            promedio = None
            estado, color = "Con observaciones NCh 409", "#ffc107"
        elif "CUMPLE" in info["evaluaciones"]:
            promedio = None
            estado, color = "Cumple norma (6,5 - 8,5)", "#28a745"
        else:
            continue

        datos_regiones[reg_norm] = {
            "promedio": promedio,
            "parametro": "pH",
            "limite": "6,5 - 8,5",
            "estado": estado,
            "color": color,
            "total_servicios": info["servicios_count"],
            "periodo": periodo,
        }

    _CACHE_AGUA = {
        "comunas": datos_comunas,
        "regiones": datos_regiones,
        "periodo": periodo,
        "error": None,
    }
    return _CACHE_AGUA