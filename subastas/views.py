from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Max
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta

from .models import Categoria, Subasta, Puja
from .serializers import (
    CategoriaSerializer, 
    SubastaSerializer, 
    SubastaDetailSerializer,
    PujaSerializer,
    PujaDetailSerializer
)

# SUBASTAS VIEWS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def subastas_list(request):
    if request.method == 'GET':
        queryset = Subasta.objects.all()
        params = request.query_params
        
        # Filtro por texto de búsqueda
        search = params.get('search', None)
        if search and len(search) < 3:
            return Response(
                {"search": "La búsqueda debe tener al menos 3 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
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
                return Response(
                    {"categoria": "Esta categoría no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(categoria=categoria)
        
        # Filtro por rango de precios
        precio_min = params.get('precio_min', None)
        precio_max = params.get('precio_max', None)
        
        # Validación de precio mínimo
        if precio_min:
            try:
                precio_min = Decimal(precio_min)
                if precio_min <= 0:
                    return Response(
                        {"precio_min": "El precio mínimo debe ser mayor que 0."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(precio_inicial__gte=precio_min)
            except (ValueError, TypeError):
                return Response(
                    {"precio_min": "El precio mínimo debe ser un número válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validación de precio máximo
        if precio_max:
            try:
                precio_max = Decimal(precio_max)
                if precio_max <= 0:
                    return Response(
                        {"precio_max": "El precio máximo debe ser mayor que 0."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(precio_inicial__lte=precio_max)
            except (ValueError, TypeError):
                return Response(
                    {"precio_max": "El precio máximo debe ser un número válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validación adicional cuando ambos precios están presentes
        if precio_min and precio_max and precio_min > precio_max:
            return Response(
                {"price_range": "El precio máximo debe ser mayor que el precio mínimo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SubastaSerializer(queryset, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Solo usuarios autenticados pueden crear subastas
        if not request.user.is_authenticated:
            return Response(
                {"error": "Debe iniciar sesión para crear una subasta."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        serializer = SubastaSerializer(data=request.data)
        if serializer.is_valid():
            # Validar que el stock y precio sean positivos
            if serializer.validated_data.get('stock', 0) <= 0:
                return Response(
                    {"stock": "El stock debe ser un número positivo."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if serializer.validated_data.get('precio_inicial', 0) <= 0:
                return Response(
                    {"precio_inicial": "El precio inicial debe ser un número positivo."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Validar la valoración entre 1 y 5
            valoracion = serializer.validated_data.get('valoracion')
            if valoracion and (valoracion < 1 or valoracion > 5):
                return Response(
                    {"valoracion": "La valoración debe estar entre 1 y 5."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Validar que la fecha de cierre sea al menos 15 días posterior a la fecha de creación
            fecha_creacion = timezone.now()
            fecha_cierre = serializer.validated_data.get('fecha_cierre')
            
            if fecha_cierre <= fecha_creacion:
                return Response(
                    {"fecha_cierre": "La fecha de cierre debe ser posterior a la fecha actual."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if fecha_cierre < (fecha_creacion + timedelta(days=15)):
                return Response(
                    {"fecha_cierre": "La fecha de cierre debe ser al menos 15 días mayor que la fecha de creación."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Al guardar, el modelo automáticamente establece el estado basado en las fechas
            serializer.save(usuario=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def subasta_detail(request, id_subasta):
    try:
        subasta = Subasta.objects.get(id=id_subasta)
    except Subasta.DoesNotExist:
        return Response(
            {"error": "La subasta no existe."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        # Actualizar el estado basado en la fecha de cierre
        if (subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta'):
            subasta.estado = 'cerrada'
            subasta.save(update_fields=['estado'])
            
        serializer = SubastaDetailSerializer(subasta)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Solo usuarios autenticados pueden actualizar subastas
        if not request.user.is_authenticated:
            return Response(
                {"error": "Debe iniciar sesión para actualizar una subasta."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        serializer = SubastaSerializer(subasta, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Solo usuarios autenticados pueden eliminar subastas
        if not request.user.is_authenticated:
            return Response(
                {"error": "Debe iniciar sesión para eliminar una subasta."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        subasta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# CATEGORIAS VIEWS
@api_view(['GET', 'POST'])
def categorias_list(request):
    if request.method == 'GET':
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CategoriaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def categoria_detail(request, id_categoria):
    categoria = get_object_or_404(Categoria, id=id_categoria)
    serializer = CategoriaSerializer(categoria)
    return Response(serializer.data)

@api_view(['PUT', 'DELETE'])
def categoria_update_delete(request, id_categoria):
    categoria = get_object_or_404(Categoria, id=id_categoria)
    
    if request.method == 'PUT':
        serializer = CategoriaSerializer(categoria, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        categoria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# PUJAS VIEWS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def pujas_list(request, id_subasta):
    try:
        subasta = Subasta.objects.get(id=id_subasta)
    except Subasta.DoesNotExist:
        return Response(
            {"error": "La subasta no existe."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Actualizar el estado de la subasta si ha cerrado
    if subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta':
        subasta.estado = 'cerrada'
        subasta.save(update_fields=['estado'])
    
    if request.method == 'GET':
        # Ordenar las pujas por cantidad descendente
        pujas = Puja.objects.filter(subasta=subasta).order_by('-cantidad')
        serializer = PujaSerializer(pujas, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Solo usuarios autenticados pueden hacer pujas
        if not request.user.is_authenticated:
            return Response(
                {"error": "Debe iniciar sesión para hacer una puja."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Verificar si la subasta está abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            return Response(
                {"error": "No se puede pujar en una subasta cerrada"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener la puja más alta actual
        puja_mas_alta = Puja.objects.filter(subasta=subasta).aggregate(Max('cantidad'))['cantidad__max']
        
        # Validar que la cantidad de la nueva puja sea mayor que la puja más alta
        nueva_cantidad = Decimal(request.data.get('cantidad', 0))
        
        if nueva_cantidad <= 0:
            return Response(
                {"cantidad": "La cantidad de la puja debe ser un número positivo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si hay pujas anteriores, verificar que la nueva puja sea mayor
        if puja_mas_alta and nueva_cantidad <= puja_mas_alta:
            return Response(
                {"cantidad": f"La puja debe ser mayor que la puja más alta actual ({puja_mas_alta})."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si no hay pujas anteriores, verificar que sea mayor que el precio inicial
        if not puja_mas_alta and nueva_cantidad <= subasta.precio_inicial:
            return Response(
                {"cantidad": f"La puja debe ser mayor que el precio inicial ({subasta.precio_inicial})."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear la serializer con los datos de la solicitud
        serializer = PujaSerializer(data=request.data, context={'request': request, 'subasta': subasta})
        if serializer.is_valid():
            serializer.save(subasta=subasta, usuario=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def puja_detail(request, id_subasta, idPuja):
    try:
        subasta = Subasta.objects.get(id=id_subasta)
        puja = Puja.objects.get(id=idPuja, subasta=subasta)
    except Subasta.DoesNotExist:
        return Response(
            {"error": "La subasta no existe."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Puja.DoesNotExist:
        return Response(
            {"error": "La puja no existe en esta subasta."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Actualizar el estado de la subasta si ha cerrado
    if subasta.fecha_cierre <= timezone.now() and subasta.estado == 'abierta':
        subasta.estado = 'cerrada'
        subasta.save(update_fields=['estado'])
    
    if request.method == 'GET':
        serializer = PujaDetailSerializer(puja)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Solo usuarios autenticados pueden actualizar pujas
        if not request.user.is_authenticated:
            return Response(
                {"error": "Debe iniciar sesión para actualizar una puja."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Verificar si la subasta está abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            return Response(
                {"error": "No se puede actualizar la puja en una subasta cerrada"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PujaSerializer(puja, data=request.data, context={'request': request, 'subasta': subasta})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Solo usuarios autenticados pueden eliminar pujas
        if not request.user.is_authenticated:
            return Response(
                {"error": "Debe iniciar sesión para eliminar una puja."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Verificar si la subasta está abierta
        if subasta.estado == 'cerrada' or subasta.fecha_cierre <= timezone.now():
            return Response(
                {"error": "No se puede eliminar la puja en una subasta cerrada"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        puja.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
