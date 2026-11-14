from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("crear/", views.crear_reporte, name="crear_reporte"),
    path("api/listar/", views.listar_reportes_api, name="listar_reportes_api"),
    path("api/tipos/", views.listar_tipos_api, name="listar_tipos_api"),
]