from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Max, Avg
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Categoria, Subasta, Puja, Rating, Comentario
from .serializers import (
    CategoriaSerializer, 
    SubastaSerializer, 
    SubastaDetailSerializer,
    PujaSerializer,
    PujaDetailSerializer,
    RatingSerializer,
    ComentarioSerializer
)
from .permissions import (
    IsOwnerOrAdmin,
    IsAdminOrReadOnly,
    IsPujaOwnerOrAdmin,
    IsAuthenticatedOrReadOnly,
    IsComentarioOwnerOrAdmin
)

# SUBASTAS VIEWS
class SubastaListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Subasta.objects.all()
    serializer_class = SubastaSerializer
    pagination_class = None  # Desactiva la paginación para esta vista

    def get_queryset(self):
        queryset = Subasta.objects.all()
        params = self.request.query_params
        
        # Filtro por texto de búsqueda
        search = params.get('search', None)
        if search and len(search) < 3:
            raise ValidationError(
                {"search": "La búsqueda debe tener al menos 3 caracteres."}
            )
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Filtro por categoría
        categoria = params.get('categoria', None)
        if categoria:
            # Verificar si la categoría existe
            if not Categoria.objects.filter(id=categoria).exists():
                raise ValidationError(
                    {"categoria": "Esta categoría no existe."}
                )
            queryset = queryset.filter(categoria=categoria)
        
        # Filtro por rango de precios
        precio_min = params.get('precio_min', None)
        precio_max = params.get('precio_max', None)
        
        # Validación de precio mínimo y máximo
        if precio_min:
            try:
                precio_min = Decimal(precio_min)
                if precio_min <= 0:
                    raise ValidationError(
                        {"precio_min": "El precio mínimo debe ser mayor que 0."}
                    )
            except (ValueError, TypeError):
                raise ValidationError(
                    {"precio_min": "El precio mínimo debe ser un número válido."}
                )
        
        if precio_max:
            try:
                precio_max = Decimal(precio_max)
                if precio_max <= 0:
                    raise ValidationError(
                        {"precio_max": "El precio máximo debe ser mayor que 0."}
                    )
            except (ValueError, TypeError):
                raise ValidationError(
                    {"precio_max": "El precio máximo debe ser un número válido."}
                )
        
        # Validación adicional cuando ambos precios están presentes
        if precio_min and precio_max and precio_min > precio_max:
            raise ValidationError(
                {"price_range": "El precio máximo debe ser mayor que el precio mínimo."}
            )
        
        # Si hay filtros de precio, filtramos por el precio actual (puja más alta o precio inicial)
        if precio_min or precio_max:
            # Obtenemos todas las subastas con sus pujas más altas
            subastas_ids = []
            
            for subasta in queryset:
                # Obtenemos la puja más alta para esta subasta
                puja_mas_alta = Puja.objects.filter(subasta=subasta).aggregate(Max('cantidad'))['cantidad__max']
                precio_actual = puja_mas_alta if puja_mas_alta else subasta.precio_inicial
                
                # Aplicamos los filtros de precio
                cumple_filtro = True
                if precio_min and precio_actual < precio_min:
                    cumple_filtro = False
                if precio_max and precio_actual > precio_max:
                    cumple_filtro = False
                    
                if cumple_filtro:
                    subastas_ids.append(subasta.id)
            
            # Filtramos las subastas utilizando los IDs que cumplen las condiciones
            queryset = queryset.filter(id__in=subastas_ids)
        
        return queryset
    
    def perform_create(self, serializer):
        # Validar que el stock y precio sean positivos
        if serializer.validated_data.get('stock', 0) <= 0:
            raise ValidationError(
                {"stock": "El stock debe ser un número positivo."}
            )
                
        if serializer.validated_data.get('precio_inicial', 0) <= 0:
            raise ValidationError(
                {"precio_inicial": "El precio inicial debe ser un número positivo."}
            )
                
        # Validar la valoración entre 1 y 5
        valoracion = serializer.validated_data.get('valoracion')
        if valoracion and (valoracion < 1 or valoracion > 5):
            raise ValidationError(
                {"valoracion": "La valoración debe estar entre 1 y 5."}
            )
                
        # Validar que la fecha de cierre sea al menos 15 días posterior a la fecha de creación
        fecha_creacion = timezone.now()
        fecha_cierre = serializer.validated_data.get('fecha_cierre')
            
        if fecha_cierre <= fecha_creacion:
            raise ValidationError(
                {"fecha_cierre": "La fecha de cierre debe ser posterior a la fecha actual."}
            )
                
        if fecha_cierre < (fecha_creacion + timedelta(days=15)):
            raise ValidationError(
                {"fecha_cierre": "La fecha de cierre debe ser al menos 15 días mayor que la fecha de creación."}
            )
            
        # Al guardar, el modelo automáticamente establece el estado basado en las fechas
        serializer.save(usuario=self.request.user)

class SubastaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrAdmin]
    queryset = Subasta.objects.all()
    serializer_class = SubastaDetailSerializer
    lookup_url_kwarg = 'id_subasta'
    
    def get_object(self):
        obj = super().get_object()
        # Actualizar el estado basado en la fecha de cierre
        if (obj.fecha_cierre <= timezone.now() and obj.estado == 'abierta'):
            obj.estado = 'cerrada'
            obj.save(update_fields=['estado'])
        return obj

# CATEGORIAS VIEWS
class CategoriaListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    pagination_class = None  # Desactiva la paginación para las categorías

class CategoriaRetrieve(generics.RetrieveAPIView):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    lookup_url_kwarg = 'id_categoria'

class CategoriaUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    lookup_url_kwarg = 'id_categoria'

# PUJAS VIEWS
class PujaListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = PujaSerializer
    pagination_class = None  # Desactiva la paginación para las pujas
    
    def get_queryset(self):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        # Actualizar el estado de la subasta si ha cerrado
        if subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta':
            subasta.estado = 'cerrada'
            subasta.save(update_fields=['estado'])
            
        # Ordenar las pujas por cantidad descendente
        return Puja.objects.filter(subasta=subasta).order_by('-cantidad')
    
    def perform_create(self, serializer):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        # Verificar si la subasta está abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            raise ValidationError(
                {"error": "No se puede pujar en una subasta cerrada"}
            )
        
        # Obtener la puja más alta actual
        puja_mas_alta = Puja.objects.filter(subasta=subasta).aggregate(Max('cantidad'))['cantidad__max']
        
        # Validar que la cantidad de la nueva puja sea mayor que la puja más alta
        nueva_cantidad = Decimal(self.request.data.get('cantidad', 0))
        
        if nueva_cantidad <= 0:
            raise ValidationError(
                {"cantidad": "La cantidad de la puja debe ser un número positivo."}
            )
        
        # Si hay pujas anteriores, verificar que la nueva puja sea mayor
        if puja_mas_alta and nueva_cantidad <= puja_mas_alta:
            raise ValidationError(
                {"cantidad": f"La puja debe ser mayor que la puja más alta actual ({puja_mas_alta})."}
            )
        
        # Si no hay pujas anteriores, verificar que sea mayor que el precio inicial
        if not puja_mas_alta and nueva_cantidad <= subasta.precio_inicial:
            raise ValidationError(
                {"cantidad": f"La puja debe ser mayor que el precio inicial ({subasta.precio_inicial})."}
            )
        
        # Pasar el objeto de usuario en lugar del nombre de usuario
        serializer.save(subasta=subasta, pujador=self.request.user)

class PujaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsPujaOwnerOrAdmin]
    serializer_class = PujaDetailSerializer
    lookup_url_kwarg = 'idPuja'
    
    def get_queryset(self):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Puja.objects.filter(subasta=subasta)
    
    def get_object(self):
        obj = super().get_object()
        subasta = obj.subasta
        
        # Actualizar el estado de la subasta si ha cerrado
        if subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta':
            subasta.estado = 'cerrada'
            subasta.save(update_fields=['estado'])
        
        return obj
    
    def perform_update(self, serializer):
        puja = self.get_object()
        subasta = puja.subasta
        
        # Verificar si la subasta está abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            raise ValidationError(
                {"error": "No se puede actualizar la puja en una subasta cerrada"}
            )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        subasta = instance.subasta
        
        # Verificar si la subasta está abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            raise ValidationError(
                {"error": "No se puede eliminar la puja en una subasta cerrada"}
            )
        
        instance.delete()

# RATINGS VIEWS
class RatingListCreate(generics.ListCreateAPIView):
    """Vista para listar valoraciones de una subasta y crear nuevas valoraciones."""
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer
    
    def get_queryset(self):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Rating.objects.filter(subasta=subasta)
    
    def get_serializer_context(self):
        """Agregar la subasta al contexto del serializador."""
        context = super().get_serializer_context()
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        context['subasta'] = subasta
        return context
    
    def perform_create(self, serializer):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        # Verificar si el usuario ya ha valorado esta subasta
        existing_rating = Rating.objects.filter(
            subasta=subasta,
            usuario=self.request.user
        ).first()
        
        if existing_rating:
            raise ValidationError(
                {"error": "Ya has valorado esta subasta. Usa PUT para actualizar tu valoración."}
            )
        
        serializer.save(subasta=subasta, usuario=self.request.user)
        
        # Actualizar la valoración media en la subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)

class RatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para recuperar, actualizar o eliminar una valoración específica."""
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer
    lookup_url_kwarg = 'id_rating'
    
    def get_queryset(self):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Rating.objects.filter(subasta=subasta)
    
    def perform_update(self, serializer):
        serializer.save()
        
        # Actualizar la valoración media en la subasta
        subasta = serializer.instance.subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)
    
    def perform_destroy(self, instance):
        subasta = instance.subasta
        
        # Verificar que el usuario es el dueño de la valoración o un admin
        if instance.usuario != self.request.user and not self.request.user.is_staff:
            raise ValidationError(
                {"error": "No tienes permisos para eliminar esta valoración."}
            )
        
        instance.delete()
        
        # Actualizar la valoración media en la subasta
        valoracion_media = subasta.get_valoracion_media()
        Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)

class UserRatingView(APIView):
    """Vista para obtener o eliminar la valoración del usuario autenticado para una subasta específica."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id_subasta):
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        try:
            rating = Rating.objects.get(subasta=subasta, usuario=request.user)
            serializer = RatingSerializer(rating)
            return Response(serializer.data)
        except Rating.DoesNotExist:
            return Response(
                {"detail": "No has valorado esta subasta aún."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, id_subasta):
        subasta = get_object_or_404(Subasta, id=id_subasta)
        
        try:
            rating = Rating.objects.get(subasta=subasta, usuario=request.user)
            rating.delete()
            
            # Actualizar la valoración media en la subasta
            valoracion_media = subasta.get_valoracion_media()
            Subasta.objects.filter(id=subasta.id).update(valoracion=valoracion_media)
            
            return Response(
                {"detail": "Tu valoración ha sido eliminada."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Rating.DoesNotExist:
            return Response(
                {"detail": "No tienes una valoración para esta subasta."},
                status=status.HTTP_404_NOT_FOUND
            )

# COMENTARIOS VIEWS
class ComentarioListCreate(generics.ListCreateAPIView):
    """Vista para listar comentarios de una subasta y crear nuevos comentarios."""
    serializer_class = ComentarioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Comentario.objects.filter(subasta=subasta)
    
    def perform_create(self, serializer):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        serializer.save(subasta=subasta, usuario=self.request.user)

class ComentarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para recuperar, actualizar o eliminar un comentario específico."""
    serializer_class = ComentarioSerializer
    permission_classes = [IsComentarioOwnerOrAdmin]
    lookup_url_kwarg = 'id_comentario'
    
    def get_queryset(self):
        id_subasta = self.kwargs.get('id_subasta')
        subasta = get_object_or_404(Subasta, id=id_subasta)
        return Comentario.objects.filter(subasta=subasta)

class UserComentarioListView(APIView):
    """Vista para obtener todos los comentarios realizados por el usuario autenticado."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Obtener todos los comentarios del usuario autenticado
        user_comentarios = Comentario.objects.filter(usuario=request.user)
        serializer = ComentarioSerializer(user_comentarios, many=True)
        return Response(serializer.data)

# VISTAS PARA USUARIO
class UserSubastaListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Obtener las subastas del usuario autenticado
        user_subastas = Subasta.objects.filter(usuario=request.user)
        serializer = SubastaSerializer(user_subastas, many=True)
        return Response(serializer.data)

class UserPujaListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Obtener las pujas realizadas por el usuario autenticado
        user_pujas = Puja.objects.filter(pujador=request.user)
        serializer = PujaSerializer(user_pujas, many=True)
        return Response(serializer.data)

class UserRatingListView(APIView):
    """Vista para obtener todas las valoraciones realizadas por el usuario autenticado."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Obtener todas las valoraciones del usuario autenticado
        user_ratings = Rating.objects.filter(usuario=request.user)
        serializer = RatingSerializer(user_ratings, many=True)
        return Response(serializer.data)
