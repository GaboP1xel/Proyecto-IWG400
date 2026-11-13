from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),
    
    # Ruta raíz redirige a la app 'mapa' (Página de inicio)
    path('', include('mapa.urls')), 
    
    # Ruta para la app 'login'
    path('login/', include('login_app.urls')),
    
    # Ruta para la app 'recopilacion'
    path('recopilacion/', include('recopilacion.urls')),
]
