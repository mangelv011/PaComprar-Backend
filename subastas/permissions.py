from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Permite editar/eliminar una subasta solo si el usuario es el propietario
    o es administrador. Cualquiera puede consultar (GET).
    """
    def has_object_permission(self, request, view, obj):
        # Permitir acceso de lectura a cualquier usuario (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True
        # Permitir si el usuario es el creador o es administrador
        return obj.usuario == request.user or request.user.is_staff

class IsAdminOrReadOnly(BasePermission):
    """
    Permite crear/editar/eliminar categorías solo a administradores.
    Cualquiera puede consultar (GET).
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsPujaOwnerOrSubastaOwnerOrAdmin(BasePermission):
    """
    Permite editar/eliminar una puja si el usuario es:
    - El propietario de la puja
    - El propietario de la subasta
    - Un administrador
    Cualquiera puede consultar (GET).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        # Permitir si es el creador de la puja, el dueño de la subasta o administrador
        return (obj.pujador == request.user.username or 
                obj.subasta.usuario == request.user or 
                request.user.is_staff)

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Permite a cualquier usuario ver las pujas,
    pero solo usuarios autenticados pueden crear pujas nuevas.
    """
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated
        )

class IsPujaOwnerOrAdmin(BasePermission):
    """
    Permite editar/eliminar una puja solo si el usuario es el propietario
    de la puja o es administrador. Cualquiera puede consultar (GET).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        # Permitir solo si es el creador de la puja o administrador
        return obj.pujador == request.user.username or request.user.is_staff
