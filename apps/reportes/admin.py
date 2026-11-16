from django.contrib import admin
from .models import ReporteCiudadano, TipoReporte, VotoReporte


@admin.register(TipoReporte)
class TipoReporteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(ReporteCiudadano)
class ReporteCiudadanoAdmin(admin.ModelAdmin):
    list_display = ("id", "categoria", "problema", "gravedad", "usuario", "estado", "fecha_creacion")
    list_filter = ("categoria", "gravedad", "estado")
    search_fields = ("problema", "descripcion", "usuario__username")


@admin.register(VotoReporte)
class VotoReporteAdmin(admin.ModelAdmin):
    list_display = ("id", "reporte", "usuario", "valor", "fecha_actualizacion")
    list_filter = ("valor",)