import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import ReporteCiudadanoForm
from .models import ReporteCiudadano, TipoReporte


@login_required
@require_http_methods(["GET", "POST"])
def crear_reporte(request):
    """
    Vista híbrida para crear un ReporteCiudadano.
    Acepta tanto peticiones JSON (fetch/AJAX desde el mapa) como formularios HTML estándar.
    """
    es_json = request.content_type == "application/json"

    if request.method == "POST":
        if es_json:
            try:
                data = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse(
                    {"ok": False, "error": "El cuerpo de la petición no es un JSON válido."},
                    status=400,
                )
            form = ReporteCiudadanoForm(data)
        else:
            form = ReporteCiudadanoForm(request.POST)

        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.usuario = request.user
            reporte.save()

            if es_json or request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": True,
                        "mensaje": "Reporte creado exitosamente.",
                        "reporte": {
                            "id": reporte.id,
                            "tipo_reporte": reporte.tipo_reporte.nombre,
                            "descripcion": reporte.descripcion,
                            "lat": reporte.lat,
                            "lon": reporte.lon,
                            "estado": reporte.estado,
                            "usuario": reporte.usuario.username,
                            "fecha_creacion": reporte.fecha_creacion.isoformat(),
                        },
                    },
                    status=201,
                )
            return redirect("/")

        if es_json or request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errores": form.errors}, status=400)

    else:
        form = ReporteCiudadanoForm()

    tipos = TipoReporte.objects.all()
    return render(
        request,
        "reportes/crear_reporte.html",
        {"form": form, "tipos_reporte": tipos},
    )


@require_GET
def listar_reportes_api(request):
    queryset = ReporteCiudadano.objects.select_related("tipo_reporte", "usuario").exclude(
        estado="rechazado"
    )

    estado = request.GET.get("estado")
    tipo_id = request.GET.get("tipo_id")

    if estado:
        queryset = queryset.filter(estado=estado)
    if tipo_id and tipo_id.isdigit():
        queryset = queryset.filter(tipo_reporte_id=int(tipo_id))

    datos = [
        {
            "id": r.id,
            "tipo_id": r.tipo_reporte_id,
            "tipo_nombre": r.tipo_reporte.nombre,
            "descripcion": r.descripcion,
            "lat": r.lat,
            "lon": r.lon,
            "estado": r.estado,
            "usuario": r.usuario.username,
            "fecha_creacion": r.fecha_creacion.isoformat(),
        }
        for r in queryset
    ]
    return JsonResponse({"ok": True, "reportes": datos}, status=200)


@require_GET
def listar_tipos_api(request):
    tipos = list(TipoReporte.objects.values("id", "nombre", "descripcion"))
    return JsonResponse({"ok": True, "tipos_reporte": tipos}, status=200)