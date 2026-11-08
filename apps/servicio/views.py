from datetime import datetime
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .extraccion import ErrorExtraccion, extraer_mediciones_nacional


class SINCAJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@require_GET
def mediciones_api(request, fuente: str):
    if fuente.lower() != "sinca":
        return JsonResponse(
            {"error": "Fuente no soportada (usa 'sinca')."},
            status=404,
            encoder=SINCAJSONEncoder,
        )

    try:
        datos = extraer_mediciones_nacional()
    except ErrorExtraccion as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=502,
            encoder=SINCAJSONEncoder,
        )

    return JsonResponse(
        datos,
        safe=False,
        encoder=SINCAJSONEncoder,
        json_dumps_params={"allow_nan": False},
    )