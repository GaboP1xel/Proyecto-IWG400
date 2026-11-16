from django.urls import path
from . import views

urlpatterns = [
    path("api/", views.listar_reportes_api, name="api_listar_reportes"),
    path("api/crear/", views.crear_reporte_api, name="api_crear_reporte"),
    path("api/<int:reporte_id>/votar/", views.votar_reporte_api, name="api_votar_reporte"),
]