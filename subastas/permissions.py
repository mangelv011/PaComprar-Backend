from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado que permite a los propietarios de un objeto o administradores
    realizar operaciones de escritura (POST, PUT, DELETE) sobre dicho objeto.
    
    Los métodos seguros (GET, HEAD, OPTIONS) están permitidos para todos los usuarios.
    
    Este permiso se utiliza principalmente para objetos como Subasta, que tienen un campo 'usuario'
    que representa al propietario.
    """
    def has_object_permission(self, request, view, obj):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) para cualquier solicitud
        if request.method in SAFE_METHODS:
            return True
        # Para otros métodos, verificar si el usuario es propietario o administrador
        return obj.usuario == request.user or request.user.is_staff

class IsAdminOrReadOnly(BasePermission):
    """
    Permiso personalizado que permite a los administradores realizar cualquier operación,
    mientras que los usuarios regulares solo pueden realizar operaciones de lectura.
    
    Este permiso controla el acceso a nivel de vista, no a nivel de objeto individual.
    Se usa para endpoints donde solo los administradores deberían poder crear, modificar o eliminar recursos.
    """
    def has_permission(self, request, view):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) para cualquier solicitud
        if request.method in SAFE_METHODS:
            return True
        # Para otros métodos, verificar si el usuario está autenticado y es administrador
        return request.user and request.user.is_staff

class IsPujaOwnerOrSubastaOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado que permite realizar operaciones de escritura a:
    - El usuario que realizó la puja (pujador)
    - El propietario de la subasta asociada a la puja
    - Cualquier administrador
    
    Este permiso se utiliza para controlar acciones sobre objetos Puja,
    garantizando que tanto el pujador como el propietario de la subasta
    puedan interactuar con la puja.
    """
    def has_object_permission(self, request, view, obj):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) para cualquier solicitud
        if request.method in SAFE_METHODS:
            return True
        # Para otros métodos, verificar si el usuario es el pujador, el propietario de la subasta, o un administrador
        return (obj.pujador == request.user or 
                obj.subasta.usuario == request.user or 
                request.user.is_staff)

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Permiso personalizado que permite operaciones de escritura solo para usuarios autenticados,
    mientras que permite operaciones de lectura para cualquier usuario.
    
    Este permiso se usa comúnmente para recursos donde cualquiera puede ver el contenido,
    pero solo los usuarios registrados pueden crear nuevo contenido o modificar existente.
    """
    def has_permission(self, request, view):
        return bool(
            # Permitir métodos seguros (GET, HEAD, OPTIONS) para cualquier solicitud
            request.method in SAFE_METHODS or
            # Para métodos no seguros, verificar que el usuario esté autenticado
            request.user and
            request.user.is_authenticated
        )

class IsPujaOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado que permite operaciones de escritura solo para:
    - El usuario que realizó la puja (pujador)
    - Administradores del sistema
    
    A diferencia de IsPujaOwnerOrSubastaOwnerOrAdmin, este permiso es más restrictivo
    al no incluir al propietario de la subasta como autorizado.
    """
    def has_object_permission(self, request, view, obj):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) para cualquier solicitud
        if request.method in SAFE_METHODS:
            return True
        # Para otros métodos, verificar si el usuario es el pujador o un administrador
        return obj.pujador == request.user or request.user.is_staff

class IsComentarioOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado que permite operaciones de escritura solo para:
    - El usuario que creó el comentario
    - Administradores del sistema
    
    Este permiso se utiliza para controlar quién puede modificar o eliminar un comentario
    existente en una subasta.
    """
    def has_object_permission(self, request, view, obj):
        # Permitir métodos seguros (GET, HEAD, OPTIONS) para cualquier solicitud
        if request.method in SAFE_METHODS:
            return True
        # Para otros métodos, verificar si el usuario es el autor del comentario o un administrador
        return obj.usuario == request.user or request.user.is_staff
