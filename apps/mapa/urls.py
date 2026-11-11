from django.urls import path
from . import views

app_name = 'mapa'

urlpatterns = [
    path('', views.mapa_view, name='index'),
]