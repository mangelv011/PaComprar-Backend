from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Max
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Categoria, Subasta, Puja, Rating, Comentario
from .serializers import (
    CategoriaSerializer, SubastaSerializer, SubastaDetailSerializer,
    PujaSerializer, PujaDetailSerializer, RatingSerializer, ComentarioSerializer
)
from .permissions import (
    IsOwnerOrAdmin, IsAdminOrReadOnly, IsPujaOwnerOrAdmin,
    IsAuthenticatedOrReadOnly, IsComentarioOwnerOrAdmin
)

# VISTAS DE SUBASTAS
class SubastaListCreate(generics.ListCreateAPIView):
    """
    Vista para listar todas las subastas y crear nuevas.
    
    GET: Obtiene lista de subastas con posibilidad de filtrado por:
    - search: Búsqueda por texto en título o descripción (mínimo 3 caracteres)
    - categoria: Filtrar por ID de categoría
    - precio_min / precio_max: Filtrar por rango de precios
    - marca: Filtrar por marca del producto
    
    POST: Crea una nueva subasta (requiere autenticación)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]  # Cualquiera puede ver, solo usuarios autenticados pueden crear
    queryset = Subasta.objects.all()
    serializer_class = SubastaSerializer
    pagination_class = None  # No paginar resultados

    def get_queryset(self):
        """
        Personaliza el queryset base aplicando los filtros según los parámetros de consulta.
        Implementa filtrado por texto, categoría y rango de precios.
        """
        queryset = Subasta.objects.all()
        params = self.request.query_params
        
        # Filtrado por texto (búsqueda)
        search = params.get('search', None)
        if search and len(search) < 3:
            raise ValidationError({"search": "La búsqueda debe tener al menos 3 caracteres."})
        if search:
            queryset = queryset.filter(Q(titulo__icontains=search) | Q(descripcion__icontains=search) |  Q(marca__icontains=search))
        
        # Filtrado por categoría
        categoria = params.get('categoria', None)
        if categoria:
            if not Categoria.objects.filter(id=categoria).exists():
                raise ValidationError({"categoria": "Esta categoría no existe."})
            queryset = queryset.filter(categoria=categoria)


        # Filtrado por estado
        estado = params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)

        # Filtrado por nombre de usuario
        username = params.get('username', None)
        if username:
            queryset = queryset.filter(usuario__username=username)


        # Filtrado por rating minimo
        rating_min = params.get('rating_min', None)
        if rating_min:
            try:
                rating_min = Decimal(rating_min)
                queryset = queryset.filter(valoracion__gt=rating_min)
            except (ValueError, TypeError):
                raise ValidationError({"rating_min": "La valoración mínima debe ser un número válido."})
            
        '''__lt: menor que (less than)
        __gte: mayor o igual que (greater than or equal)
        __lte: menor o igual que (less than or equal)
        __exact: igualdad exacta'''

        
        # Filtrado por rango de precios
        precio_min = params.get('precio_min', None)
        precio_max = params.get('precio_max', None)
        
        # Validación del precio mínimo
        if precio_min:
            try:
                precio_min = Decimal(precio_min)
                if precio_min <= 0:
                    raise ValidationError({"precio_min": "El precio mínimo debe ser mayor que 0."})
            except (ValueError, TypeError):
                raise ValidationError({"precio_min": "El precio mínimo debe ser un número válido."})
        
        # Validación del precio máximo
        if precio_max:
            try:
                precio_max = Decimal(precio_max)
                if precio_max <= 0:
                    raise ValidationError({"precio_max": "El precio máximo debe ser mayor que 0."})
            except (ValueError, TypeError):
                raise ValidationError({"precio_max": "El precio máximo debe ser un número válido."})
        
        # Verificar que el rango sea coherente
        if precio_min and precio_max and precio_min > precio_max:
            raise ValidationError({"price_range": "El precio máximo debe ser mayor que el precio mínimo."})
        
        # Aplicar filtro de precio considerando pujas existentes
        if precio_min or precio_max:
            subastas_ids = []
            for subasta in queryset:
                # Obtener la puja más alta para esta subasta
                puja_mas_alta = Puja.objects.filter(subasta=subasta).aggregate(Max('cantidad'))['cantidad__max']
                # El precio actual es la puja más alta o el precio inicial si no hay pujas
                precio_actual = puja_mas_alta if puja_mas_alta else subasta.precio_inicial
                
                # Verificar si cumple con el filtro de precio
                cumple_filtro = True
                if precio_min and precio_actual < precio_min:
                    cumple_filtro = False
                if precio_max and precio_actual > precio_max:
                    cumple_filtro = False
                    
                if cumple_filtro:
                    subastas_ids.append(subasta.id)
            
            # Filtrar el queryset por los IDs que cumplen el criterio de precio
            queryset = queryset.filter(id__in=subastas_ids)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Al crear una subasta, asigna automáticamente el usuario autenticado como propietario.
        """
        serializer.save(usuario=self.request.user)

class SubastaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para gestionar una subasta específica.
    
    GET: Obtiene detalles de una subasta (incluye información detallada como pujas y valoraciones)
    PUT/PATCH: Actualiza una subasta (solo propietario o admin)
    DELETE: Elimina una subasta (solo propietario o admin)
    """
    permission_classes = [IsOwnerOrAdmin]  # Solo el propietario o administradores pueden modificar/eliminar
    queryset = Subasta.objects.all()
    serializer_class = SubastaDetailSerializer
    lookup_url_kwarg = 'id_subasta'  # Parámetro URL para identificar la subasta
    
    def get_object(self):
        """
        Sobrescribe el método para actualizar automáticamente el estado de la subasta
        si ha pasado su fecha de cierre pero aún aparece como 'abierta'.
        """
        obj = super().get_object()
        if (obj.fecha_cierre <= timezone.now() and obj.estado == 'abierta'):
            obj.estado = 'cerrada'
            obj.save(update_fields=['estado'])
        return obj

# VISTAS DE CATEGORÍAS
class CategoriaListCreate(generics.ListCreateAPIView):
    """
    Vista para listar todas las categorías y crear nuevas.
    
    GET: Obtiene lista de todas las categorías
    POST: Crea una nueva categoría (solo administradores)
    """
    permission_classes = [IsAdminOrReadOnly]  # Solo administradores pueden crear categorías
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    pagination_class = None  # No paginar resultados

class CategoriaRetrieve(generics.RetrieveAPIView):
    """
    Vista para obtener detalles de una categoría específica (solo lectura).
    
    GET: Obtiene detalles de una categoría específica
    """
    permission_classes = [IsAdminOrReadOnly]
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    lookup_url_kwarg = 'id_categoria'  # Parámetro URL para identificar la categoría

class CategoriaUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para actualizar o eliminar una categoría específica.
    
    GET: Obtiene detalles de una categoría específica
    PUT/PATCH: Actualiza una categoría (solo administradores)
    DELETE: Elimina una categoría (solo administradores)
    """
    permission_classes = [IsAdminOrReadOnly]  # Solo administradores pueden modificar/eliminar
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    lookup_url_kwarg = 'id_categoria'  # Parámetro URL para identificar la categoría

# VISTAS DE PUJAS
class PujaListCreate(generics.ListCreateAPIView):
    """
    Vista para listar todas las pujas de una subasta y crear nuevas.
    
    GET: Obtiene lista de pujas para una subasta específica
    POST: Crea una nueva puja para la subasta (requiere autenticación)
    
    Las pujas están ordenadas por cantidad (de mayor a menor).
    """
    permission_classes = [IsAuthenticatedOrReadOnly]  # Cualquiera puede ver, solo usuarios autenticados pueden pujar
    serializer_class = PujaSerializer
    pagination_class = None  # No paginar resultados
    
    def get_queryset(self):
        """
        Obtiene todas las pujas de una subasta específica.
        También actualiza el estado de la subasta si ha pasado su fecha de cierre.
        """
        id_subasta = self.kwargs.get('id_subasta')  # Obtener ID de la subasta desde la URL
        subasta = get_object_or_404(Subasta, id=id_subasta)  # Obtener objeto subasta o 404
        
        # Actualizar estado de la subasta si ha expirado
        if subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta':
            subasta.estado = 'cerrada'
            subasta.save(update_fields=['estado'])
            
        # Devolver pujas ordenadas por cantidad descendente
        return Puja.objects.filter(subasta=subasta).order_by('-cantidad')
    
    def perform_create(self, serializer):
        """
        Crea una nueva puja verificando condiciones de validez:
        - La subasta debe estar abierta
        - La cantidad debe ser positiva
        - La cantidad debe ser mayor que la puja más alta actual o el precio inicial
        """
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        # Verificar que la subasta esté abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            raise ValidationError({"error": "No se puede pujar en una subasta cerrada"})
        
        # Obtener puja más alta actual
        puja_mas_alta = Puja.objects.filter(subasta=subasta).aggregate(Max('cantidad'))['cantidad__max']
        nueva_cantidad = Decimal(self.request.data.get('cantidad', 0))
        
        # Validar que la cantidad sea positiva
        if nueva_cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad de la puja debe ser un número positivo."})
        
        # Validar que supere la puja más alta si existe
        if puja_mas_alta and nueva_cantidad <= puja_mas_alta:
            raise ValidationError({"cantidad": f"La puja debe ser mayor que la puja más alta actual ({puja_mas_alta})."})
        
        # Validar que supere el precio inicial si no hay pujas previas
        if not puja_mas_alta and nueva_cantidad <= subasta.precio_inicial:
            raise ValidationError({"cantidad": f"La puja debe ser mayor que el precio inicial ({subasta.precio_inicial})."})
        
        # Guardar la puja con la subasta y el usuario autenticado
        serializer.save(subasta=subasta, pujador=self.request.user)

class PujaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para gestionar una puja específica.
    
    GET: Obtiene detalles de una puja específica
    PUT/PATCH: Actualiza una puja (solo propietario o admin)
    DELETE: Elimina una puja (solo propietario o admin)
    
    Solo se permite modificar o eliminar pujas en subastas abiertas.
    """
    permission_classes = [IsPujaOwnerOrAdmin]  # Solo el autor de la puja o administradores
    serializer_class = PujaDetailSerializer
    lookup_url_kwarg = 'idPuja'  # Parámetro URL para identificar la puja
    
    def get_queryset(self):
        """
        Obtiene el queryset filtrado por la subasta especificada en la URL.
        """
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Puja.objects.filter(subasta=subasta)
    
    def get_object(self):
        """
        Obtiene la puja y actualiza el estado de la subasta si ha pasado su fecha de cierre.
        """
        obj = super().get_object()
        subasta = obj.subasta
        
        # Actualizar estado de la subasta si ha expirado
        if subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta':
            subasta.estado = 'cerrada'
            subasta.save(update_fields=['estado'])
        
        return obj
    
    def perform_update(self, serializer):
        """
        Actualiza la puja verificando que la subasta esté abierta.
        """
        puja = self.get_object()
        subasta = puja.subasta
        
        # Verificar que la subasta esté abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            raise ValidationError({"error": "No se puede actualizar la puja en una subasta cerrada"})
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Elimina la puja verificando que la subasta esté abierta.
        """
        subasta = instance.subasta
        
        # Verificar que la subasta esté abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            raise ValidationError({"error": "No se puede eliminar la puja en una subasta cerrada"})
        
        instance.delete()

# VISTAS DE VALORACIONES (RATINGS)
class RatingListCreate(generics.ListCreateAPIView):
    """
    Vista para listar todas las valoraciones de una subasta y crear nuevas.
    
    GET: Obtiene lista de valoraciones para una subasta específica
    POST: Crea una nueva valoración para la subasta (requiere autenticación)
    
    Cada usuario solo puede tener una valoración por subasta.
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    serializer_class = RatingSerializer
    
    def get_queryset(self):
        """
        Obtiene todas las valoraciones para una subasta específica.
        """
        id_subasta = self.kwargs.get('id_subasta')  # Obtener ID de la subasta desde la URL
        subasta = get_object_or_404(Subasta, id=id_subasta)  # Obtener objeto subasta o 404
        return Rating.objects.filter(subasta=subasta)
    
    def get_serializer_context(self):
        """
        Añade la subasta al contexto del serializador para que pueda acceder a ella.
        """
        context = super().get_serializer_context()
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        context['subasta'] = subasta
        return context
    
    def perform_create(self, serializer):
        """
        Crea una nueva valoración verificando que el usuario no haya valorado antes esta subasta.
        Actualiza la valoración media de la subasta después de crear la valoración.
        """
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        # Verificar si el usuario ya ha valorado esta subasta
        existing_rating = Rating.objects.filter(
            subasta=subasta,
            usuario=self.request.user
        ).first()
        
        # Si ya existe una valoración, mostrar error sugiriendo usar PUT para actualizar
        if existing_rating:
            raise ValidationError({"error": "Ya has valorado esta subasta. Usa PUT para actualizar tu valoración."})
        
        # Guardar la nueva valoración
        serializer.save(subasta=subasta, usuario=self.request.user)
        
        # Actualizar la valoración media de la subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)

class RatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para gestionar una valoración específica.
    
    GET: Obtiene detalles de una valoración específica
    PUT/PATCH: Actualiza una valoración (solo propietario o admin)
    DELETE: Elimina una valoración (solo propietario o admin)
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    serializer_class = RatingSerializer
    lookup_url_kwarg = 'id_rating'  # Parámetro URL para identificar la valoración
    
    def get_queryset(self):
        """
        Obtiene el queryset filtrado por la subasta especificada en la URL.
        """
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Rating.objects.filter(subasta=subasta)
    
    def perform_update(self, serializer):
        """
        Actualiza la valoración y recalcula la valoración media de la subasta.
        """
        serializer.save()
        
        # Actualizar la valoración media de la subasta
        subasta = serializer.instance.subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)
        
        subasta = serializer.instance.subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)
    
    def perform_destroy(self, instance):
        """
        Elimina la valoración y recalcula la valoración media de la subasta.
        Solo permite al propietario o administradores eliminar la valoración.
        """
        subasta = instance.subasta
        
        # Verificar permisos (seguridad adicional)
        if instance.usuario != self.request.user and not self.request.user.is_staff:
            raise ValidationError({"error": "No tienes permisos para eliminar esta valoración."})
        
        # Eliminar la valoración
        instance.delete()
        
        # Actualizar la valoración media de la subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)

class UserRatingView(APIView):
    """
    Vista para gestionar la valoración del usuario autenticado para una subasta específica.
    
    GET: Obtiene la valoración actual del usuario para la subasta
    DELETE: Elimina la valoración del usuario para la subasta
    
    Esta vista es útil para que los usuarios gestionen su propia valoración
    sin necesidad de conocer el ID específico de la valoración.
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request, id_subasta):
        """
        Obtiene la valoración del usuario autenticado para una subasta específica.
        """
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        try:
            # Buscar valoración del usuario actual
            rating = Rating.objects.get(subasta=subasta, usuario=request.user)
            serializer = RatingSerializer(rating)
            return Response(serializer.data)
        except Rating.DoesNotExist:
            return Response({"detail": "No has valorado esta subasta aún."}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, id_subasta):
        """
        Elimina la valoración del usuario autenticado para una subasta específica.
        """
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        try:
            # Buscar valoración del usuario actual
            rating = Rating.objects.get(subasta=subasta, usuario=request.user)
            # Eliminar la valoración
            rating.delete()
            
            # Actualizar la valoración media de la subasta
            valoracion_media = subasta.get_valoracion_media()
            Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)
            
            return Response({"detail": "Tu valoración ha sido eliminada."}, status=status.HTTP_204_NO_CONTENT)
        except Rating.DoesNotExist:
            return Response({"detail": "No tienes una valoración para esta subasta."}, status=status.HTTP_404_NOT_FOUND)

# VISTAS DE COMENTARIOS
class ComentarioListCreate(generics.ListCreateAPIView):
    """
    Vista para listar todos los comentarios de una subasta y crear nuevos.
    
    GET: Obtiene lista de comentarios para una subasta específica
    POST: Crea un nuevo comentario para la subasta (requiere autenticación)
    """
    serializer_class = ComentarioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Cualquiera puede ver, solo usuarios autenticados pueden comentar
    pagination_class = None  # No paginar resultados
    
    def get_queryset(self):
        """
        Obtiene todos los comentarios para una subasta específica.
        """
        id_subasta = self.kwargs.get('id_subasta')  # Obtener ID de la subasta desde la URL
        subasta = get_object_or_404(Subasta, id=id_subasta)  # Obtener objeto subasta o 404
        return Comentario.objects.filter(subasta=subasta)
    
    def get_serializer_context(self):
        """
        Añade la subasta al contexto del serializador para que pueda acceder a ella.
        """
        context = super().get_serializer_context()
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        context['subasta'] = subasta
        return context
    
    def perform_create(self, serializer):
        """
        Crea un nuevo comentario asociado a la subasta y al usuario autenticado.
        """
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        serializer.save(subasta=subasta, usuario=self.request.user)

class ComentarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para gestionar un comentario específico.
    
    GET: Obtiene detalles de un comentario específico
    PUT/PATCH: Actualiza un comentario (solo propietario o admin)
    DELETE: Elimina un comentario (solo propietario o admin)
    """
    serializer_class = ComentarioSerializer
    permission_classes = [IsComentarioOwnerOrAdmin]  # Solo el autor del comentario o administradores
    lookup_url_kwarg = 'id_comentario'  # Parámetro URL para identificar el comentario
    
    def get_queryset(self):
        """
        Obtiene el queryset filtrado por la subasta especificada en la URL.
        """
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Comentario.objects.filter(subasta=subasta)

# VISTAS ESPECÍFICAS PARA USUARIOS
class UserComentarioListView(APIView):
    """
    Vista para listar todos los comentarios realizados por el usuario autenticado.
    
    GET: Obtiene lista de todos los comentarios hechos por el usuario autenticado
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request, *args, **kwargs):
        """
        Obtiene y serializa todos los comentarios del usuario autenticado.
        """
        user_comentarios = Comentario.objects.filter(usuario=request.user)
        serializer = ComentarioSerializer(user_comentarios, many=True)
        return Response(serializer.data)

class UserSubastaListView(APIView):
    """
    Vista para listar todas las subastas creadas por el usuario autenticado.
    
    GET: Obtiene lista de todas las subastas creadas por el usuario autenticado
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request, *args, **kwargs):
        """
        Obtiene y serializa todas las subastas creadas por el usuario autenticado.
        """
        user_subastas = Subasta.objects.filter(usuario=request.user)
        serializer = SubastaSerializer(user_subastas, many=True)
        return Response(serializer.data)

class UserPujaListView(APIView):
    """
    Vista para listar todas las pujas realizadas por el usuario autenticado.
    
    GET: Obtiene lista de todas las pujas realizadas por el usuario autenticado
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request, *args, **kwargs):
        """
        Obtiene y serializa todas las pujas realizadas por el usuario autenticado.
        """
        user_pujas = Puja.objects.filter(pujador=request.user)
        serializer = PujaSerializer(user_pujas, many=True)
        return Response(serializer.data)

class UserRatingListView(APIView):
    """
    Vista para listar todas las valoraciones realizadas por el usuario autenticado.
    
    GET: Obtiene lista de todas las valoraciones realizadas por el usuario autenticado
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request, *args, **kwargs):
        """
        Obtiene y serializa todas las valoraciones realizadas por el usuario autenticado.
        """
        user_ratings = Rating.objects.filter(usuario=request.user)
        serializer = RatingSerializer(user_ratings, many=True)
        return Response(serializer.data)
