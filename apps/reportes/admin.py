from django.contrib import admin
from .models import ReporteBasura


@admin.register(ReporteBasura)
class ReporteBasuraAdmin(admin.ModelAdmin):
    list_display = ('id', 'ubicacion', 'estado', 'usuario', 'lat', 'lon', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('ubicacion', 'descripcion', 'usuario__username')
    readonly_fields = ('fecha_creacion',)
    list_editable = ('estado',)