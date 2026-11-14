from django.contrib import admin
from .models import ReporteCiudadano, TipoReporte


@admin.register(TipoReporte)
class TipoReporteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(ReporteCiudadano)
class ReporteCiudadanoAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo_reporte", "usuario", "estado", "fecha_creacion")
    list_filter = ("estado", "tipo_reporte")
    search_fields = ("descripcion", "usuario__username")