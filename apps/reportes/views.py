import json
from django.shortcuts import render
from django.http import JsonResponse
from .forms import ReporteBasuraForm


def registrar_reporte(request):
    es_json = request.content_type == 'application/json'
    es_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or es_json

    if request.method == 'POST':
        if es_json:
            try:
                datos = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'estado': 'error', 'mensaje': 'Formato JSON invalido'},
                    status=400
                )
        else:
            datos = request.POST

        form = ReporteBasuraForm(datos)

        if form.is_valid():
            reporte = form.save(commit=False)

            if request.user.is_authenticated:
                reporte.usuario = request.user

            reporte.save()
            mensaje_exito = f'Reporte guardado para {reporte.ubicacion}'

            if es_ajax:
                return JsonResponse(
                    {'estado': 'exito', 'mensaje': mensaje_exito, 'id': reporte.id},
                    status=201
                )

            contexto = {
                'titulo': 'Reportar Basura o Contaminacion',
                'form': ReporteBasuraForm(),
                'mensaje_exito': mensaje_exito
            }
            return render(request, 'reportes/formulario.html', contexto)

        if es_ajax:
            return JsonResponse(
                {'estado': 'error', 'errores': form.errors},
                status=400
            )

        contexto = {
            'titulo': 'Reportar Basura o Contaminacion',
            'form': form
        }
        return render(request, 'reportes/formulario.html', contexto, status=400)

    contexto = {
        'titulo': 'Reportar Basura o Contaminacion',
        'form': ReporteBasuraForm()
    }
    return render(request, 'reportes/formulario.html', contexto)