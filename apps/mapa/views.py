from django.shortcuts import render
from .cruceDataAire import obtener_datos_aire_mapa
from .cruceDataAgua import obtener_datos_agua_mapa


def mapa_view(request):
    aire = obtener_datos_aire_mapa()
    agua = obtener_datos_agua_mapa()

    print(
        f"SINCA -> Comunas: {len(aire['comunas'])} | Regiones: {len(aire['regiones'])} | Error: {aire['error']}\n"
        f"SISS  -> Comunas: {len(agua['comunas'])} | Regiones: {len(agua['regiones'])} | Error: {agua['error']}"
    )

    contexto = {
        "titulo": "Mapa de Calidad Ambiental en Chile",
        "aire_comunas": aire["comunas"],
        "aire_regiones": aire["regiones"],
        "agua_comunas": agua["comunas"],
        "agua_regiones": agua["regiones"],
    }
    return render(request, "mapa.html", contexto)