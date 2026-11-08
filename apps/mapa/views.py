import json
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render

from apps.recopilacion.extraccion import extraer_mediciones_nacional


def clasificar_calidad_aire(parametro, valor):
    nombre = parametro.lower().replace(" ", "").replace(".", "").replace(",", "")
    if nombre not in {"mp25", "pm25"}:
        return "Sin clasificación", "#6c757d"

    valor = Decimal(str(valor))
    if valor <= 49:
        return "Bueno", "#28a745"
    if valor <= 79:
        return "Regular", "#ffc107"
    if valor <= 109:
        return "Alerta", "#fd7e14"
    if valor <= 169:
        return "Preemergencia", "#dc3545"
    return "Emergencia", "#6f42c1"


def mapa_view(request):
    mediciones = extraer_mediciones_nacional()
    datos_estaciones = []

    for medicion in mediciones:
        estado, color = clasificar_calidad_aire(
            medicion["parametro"],
            medicion["valor"],
        )
        fecha = medicion["fecha"]

        datos_estaciones.append({
            "estacion": medicion["estacion"],
            "parametro": medicion["parametro"],
            "valor": medicion["valor"],
            "unidad": medicion["unidad"],
            "estado": estado,
            "color": color,
            "lat": medicion["lat"],
            "lon": medicion["lon"],
            "fecha": fecha.strftime("%d/%m/%Y %H:%M") if fecha else "",
        })

    contexto = {
        "titulo": "Mapa de Calidad Ambiental en Chile",
        "estaciones_json": json.dumps(datos_estaciones, cls=DjangoJSONEncoder),
        "total_estaciones": len(datos_estaciones),
    }
    return render(request, "mapa/index.html", contexto)