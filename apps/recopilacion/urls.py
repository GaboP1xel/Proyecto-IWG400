from django.urls import path

from .views import mediciones_api

urlpatterns = [
    path("api/mediciones/<str:fuente>/", mediciones_api, name="api_mediciones"),
]
