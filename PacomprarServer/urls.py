"""
URL configuration for PacomprarServer project.

Esta configuración central de URLs define las rutas principales de la API y conecta
con las URLs de las aplicaciones individuales (subastas, usuarios).
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views import CustomTokenObtainPairView

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # API para gestión de usuarios (registro, autenticación, perfil, etc.)
    path("api/usuarios/", include("usuarios.urls")),
    
    # API principal del sistema de subastas (subastas, categorías, pujas, etc.)
    path('api/', include('subastas.urls')),
    
    # Endpoints para la autenticación JWT
    # Obtener token inicial (login)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Refrescar token sin requerir credenciales
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
