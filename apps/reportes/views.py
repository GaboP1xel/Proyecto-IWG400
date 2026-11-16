import json
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import ReporteCiudadano, TipoReporte, VotoReporte

OPCIONES_VALIDAS = {
    "agua": {
        "Zona de desperdicios líquidos",
        "Agua contaminada por químicos",
        "Agua con residuos sólidos / contaminación humana",
    },
    "aire": {
        "Aire pesado / humo",
        "Mal olor",
    },
    "residuos": {
        "Microbasural / acumulación de basura",
        "Escombros o residuos voluminosos",
        "Contenedor / punto de acopio desbordado",
        "General",
    },
}


def _serializar_reporte(reporte, user=None, likes=None, dislikes=None, mi_voto=None):
    if likes is None:
        likes = reporte.votos.filter(valor=VotoReporte.VALOR_LIKE).count()
    if dislikes is None:
        dislikes = reporte.votos.filter(valor=VotoReporte.VALOR_DISLIKE).count()
    if mi_voto is None:
        if user and user.is_authenticated:
            voto_obj = reporte.votos.filter(usuario=user).first()
            mi_voto = voto_obj.valor if voto_obj else 0
        else:
            mi_voto = 0

    return {
        "id": reporte.id,
        "usuario": reporte.usuario.username,
        "categoria": reporte.categoria,
        "categoria_display": reporte.get_categoria_display(),
        "problema": reporte.problema,
        "gravedad": reporte.gravedad,
        "lat": reporte.lat,
        "lon": reporte.lon,
        "fecha": reporte.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
        "likes": likes,
        "dislikes": dislikes,
        "mi_voto": mi_voto,
    }


@require_GET
def listar_reportes_api(request):
    queryset = (
        ReporteCiudadano.objects.exclude(estado=ReporteCiudadano.ESTADO_RECHAZADO)
        .select_related("usuario")
        .annotate(
            total_likes=Count("votos", filter=Q(votos__valor=VotoReporte.VALOR_LIKE)),
            total_dislikes=Count("votos", filter=Q(votos__valor=VotoReporte.VALOR_DISLIKE)),
        )
    )

    votos_usuario = {}
    if request.user.is_authenticated:
        votos_usuario = dict(
            VotoReporte.objects.filter(usuario=request.user).values_list("reporte_id", "valor")
        )

    data = [
        _serializar_reporte(
            r,
            likes=r.total_likes,
            dislikes=r.total_dislikes,
            mi_voto=votos_usuario.get(r.id, 0),
        )
        for r in queryset
    ]
    return JsonResponse({"reportes": data})


@require_POST
def crear_reporte_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Debes iniciar sesión para reportar."}, status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)

    categoria = str(payload.get("categoria", "")).strip().lower()
    problema = str(payload.get("problema", "")).strip()

    try:
        gravedad = int(payload.get("gravedad", 0))
        lat = float(payload.get("lat"))
        lon = float(payload.get("lon"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Coordenadas o gravedad inválidas."}, status=400)

    if categoria not in OPCIONES_VALIDAS:
        return JsonResponse({"ok": False, "error": "Categoría no válida."}, status=400)
    if problema not in OPCIONES_VALIDAS[categoria]:
        return JsonResponse({"ok": False, "error": "Problema no válido para la categoría."}, status=400)
    if gravedad not in (1, 2, 3):
        return JsonResponse({"ok": False, "error": "La gravedad debe estar entre 1 y 3."}, status=400)
    if not (-56.5 <= lat <= -17.0 and -110.0 <= lon <= -66.0):
        return JsonResponse({"ok": False, "error": "Ubicación fuera de territorio chileno."}, status=400)

    nombre_tipo = dict(ReporteCiudadano.CATEGORIAS)[categoria]
    tipo_obj, _ = TipoReporte.objects.get_or_create(nombre=nombre_tipo)

    reporte = ReporteCiudadano.objects.create(
        usuario=request.user,
        tipo_reporte=tipo_obj,
        categoria=categoria,
        problema=problema,
        gravedad=gravedad,
        lat=lat,
        lon=lon,
    )

    return JsonResponse(
        {"ok": True, "reporte": _serializar_reporte(reporte, user=request.user, likes=0, dislikes=0, mi_voto=0)},
        status=201,
    )


@require_POST
def votar_reporte_api(request, reporte_id):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Debes iniciar sesión para votar."}, status=401)

    reporte = get_object_or_404(ReporteCiudadano, id=reporte_id)

    try:
        payload = json.loads(request.body)
        valor = int(payload.get("valor"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Voto inválido."}, status=400)

    if valor not in (VotoReporte.VALOR_LIKE, VotoReporte.VALOR_DISLIKE):
        return JsonResponse({"ok": False, "error": "El valor debe ser 1 o -1."}, status=400)

    voto_existente = VotoReporte.objects.filter(reporte=reporte, usuario=request.user).first()

    if voto_existente is None:
        VotoReporte.objects.create(reporte=reporte, usuario=request.user, valor=valor)
        mi_voto = valor
    elif voto_existente.valor == valor:
        # Si vuelve a pulsar el mismo botón, revoca su voto
        voto_existente.delete()
        mi_voto = 0
    else:
        # Cambia de Apoyar a No apoyar (o viceversa)
        voto_existente.valor = valor
        voto_existente.save(update_fields=["valor", "fecha_actualizacion"])
        mi_voto = valor

    likes = reporte.votos.filter(valor=VotoReporte.VALOR_LIKE).count()
    dislikes = reporte.votos.filter(valor=VotoReporte.VALOR_DISLIKE).count()

    return JsonResponse({
        "ok": True,
        "likes": likes,
        "dislikes": dislikes,
        "mi_voto": mi_voto,
    })