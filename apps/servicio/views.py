from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .extraccion import extraer_mediciones_nacional

FUENTES = {
    "sinca": "https://sinca.mma.gob.cl/index.php/...",  # URL CSV real
    "dga": "https://snia.mop.gob.cl/...",                # URL CSV real
}


@require_GET
def mediciones_api(request, fuente: str):
    url = FUENTES.get(fuente.lower())
    if url is None:
        return JsonResponse({"error": "Fuente no soportada (usa 'sinca' o 'dga')"}, status=404)

    datos = extraer_mediciones_nacional()
    return JsonResponse({"fuente": fuente, "total": len(datos), "datos": datos}, json_dumps_params={"default": str})