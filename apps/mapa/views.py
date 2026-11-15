from django.shortcuts import render
from .cruceDataAire import obtener_datos_aire_mapa


def mapa_view(request):
    aire = obtener_datos_aire_mapa()

    contexto = {
        "titulo": "Mapa de Calidad Ambiental en Chile",
        "aire_comunas": aire["comunas"],
        "aire_regiones": aire["regiones"],
        "aire_error": aire["error"],
    }
    return render(request, "mapa.html", contexto)