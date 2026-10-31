from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('registrar/', views.registrar_reporte, name='registrar_reporte'),
]