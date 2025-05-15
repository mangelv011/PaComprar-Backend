from django.urls import path
from .views import UserRegisterView, UserListView, UserRetrieveUpdateDestroyView, LogoutView, UserProfileView, ChangePasswordView

app_name="usuarios"
urlpatterns = [
    # Registro de nuevos usuarios
    path('register/', UserRegisterView.as_view(), name='user-register'),
    
    # Listado de todos los usuarios (acceso restringido a administradores)
    path('', UserListView.as_view(), name='user-list'),
    
    # Detalles, actualización y eliminación de un usuario específico (según permisos)
    path('<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    
    # Perfil del usuario autenticado (obtener y actualizar información propia)
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Cambiar contraseña del usuario autenticado
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Cerrar sesión (invalidar token JWT)
    path('log-out/', LogoutView.as_view(), name='log-out')
]