from django.shortcuts import render

import json
from django.shortcuts import render
from .models import MedicionAire

def clasificar_calidad_aire(valor):
    """
    Asigna una categoría y color de semáforo según el valor de MP2.5 (Norma chilena MMA)
    """
    if valor <= 49:
        return 'Bueno', '#28a745'          # Verde
    elif valor <= 79:
        return 'Regular', '#ffc107'        # Amarillo
    elif valor <= 109:
        return 'Alerta', '#fd7e14'         # Naranja
    elif valor <= 169:
        return 'Preemergencia', '#dc3545'   # Rojo
    else:
        return 'Emergencia', '#6f42c1'      # Morado

def mapa_view(request):

    # 1. Obtenemos todas las mediciones de la base de datos
    mediciones = MedicionAire.objects.all()

    # 2. Las convertimos a formato lista para que JavaScript las entienda
    datos_estaciones = []
    for m in mediciones:
        estado, color = clasificar_calidad_aire(m.valor)
        datos_estaciones.append({
            'estacion': m.estacion,
            'parametro': m.parametro,
            'valor': m.valor,
            'unidad': m.unidad,
            'estado': estado,
            'color': color,
            'lat': m.lat,
            'lon': m.lon,
            'fecha': m.fecha.strftime('%d/%m/%Y %H:%M') if m.fecha else ''
        })

    # 3. Enviamos los datos empaquetados como JSON al HTML
    contexto = {
        'titulo': 'Mapa de Calidad Ambiental en Chile',
        'estaciones_json': json.dumps(datos_estaciones),
        'total_estaciones': len(datos_estaciones),
    }
    return render(request, 'mapa/index.html', contexto)