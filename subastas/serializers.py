from rest_framework import serializers
from .models import Categoria, Subasta, Puja
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class SubastaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subasta
        fields = '__all__'
        read_only_fields = ['estado', 'fecha_creacion']
    
    def validate(self, data):
        # Validar que la fecha de cierre sea posterior a la fecha actual
        if 'fecha_cierre' in data and data['fecha_cierre'] <= timezone.now():
            raise serializers.ValidationError({
                'fecha_cierre': 'La fecha de cierre debe ser posterior a la fecha actual'
            })
        
        # Validar que la fecha de cierre sea al menos 15 días después de la fecha actual
        min_fecha_cierre = timezone.now() + timedelta(days=15)
        if 'fecha_cierre' in data and data['fecha_cierre'] < min_fecha_cierre:
            raise serializers.ValidationError({
                'fecha_cierre': 'La fecha de cierre debe ser al menos 15 días después de la fecha actual'
            })
        
        # Validar que el precio sea positivo
        if 'precio_inicial' in data and data['precio_inicial'] <= 0:
            raise serializers.ValidationError({
                'precio_inicial': 'El precio debe ser mayor que 0'
            })
        
        # Validar que el stock sea positivo
        if 'stock' in data and data['stock'] <= 0:
            raise serializers.ValidationError({
                'stock': 'El stock debe ser al menos 1'
            })
        
        # Validar que la valoración esté entre 1 y 5
        if 'valoracion' in data:
            if data['valoracion'] < 1 or data['valoracion'] > 5:
                raise serializers.ValidationError({
                    'valoracion': 'La valoración debe estar entre 1 y 5'
                })
        
        return data
        
class SubastaDetailSerializer(serializers.ModelSerializer):
    pujas = serializers.SerializerMethodField()
    categoria_nombre = serializers.SerializerMethodField()
    estado_actual = serializers.SerializerMethodField()
    
    class Meta:
        model = Subasta
        fields = '__all__'
        
    def get_pujas(self, obj):
        # Obtener todas las pujas ordenadas por cantidad descendente
        pujas = obj.pujas.all().order_by('-cantidad')
        return PujaSerializer(pujas, many=True).data
    
    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre
    
    def get_estado_actual(self, obj):
        # Calcular el estado actual basado en la fecha de cierre
        if obj.fecha_cierre <= timezone.now():
            return 'cerrada'
        return 'abierta'

class PujaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Puja
        fields = '__all__'
        read_only_fields = ['subasta', 'fecha_puja']
    
    def validate(self, data):
        # Si estamos actualizando una puja existente
        request = self.context.get('request')
        if request and request.method == 'PUT':
            # Obtener la subasta asociada a la puja
            subasta = self.instance.subasta
            
            # Verificar que la subasta esté abierta
            if subasta.fecha_cierre <= timezone.now() or subasta.estado == 'cerrada':
                raise serializers.ValidationError("No se puede actualizar la puja en una subasta cerrada")
        
        # Validar que la cantidad sea positiva
        if 'cantidad' in data and data['cantidad'] <= 0:
            raise serializers.ValidationError({
                'cantidad': 'La cantidad de la puja debe ser mayor que 0'
            })
        
        # Validar que la cantidad sea mayor que la puja más alta actual
        if self.context.get('subasta') and 'cantidad' in data:
            subasta = self.context.get('subasta')
            
            # Obtener la puja más alta actual
            puja_mas_alta = subasta.pujas.aggregate(max_cantidad=Max('cantidad'))
            max_cantidad = puja_mas_alta.get('max_cantidad') if puja_mas_alta.get('max_cantidad') else 0
            
            # Si no hay pujas, la cantidad debe ser al menos igual al precio inicial
            if max_cantidad == 0 and data['cantidad'] < subasta.precio_inicial:
                raise serializers.ValidationError({
                    'cantidad': f'La cantidad debe ser al menos igual al precio inicial: {subasta.precio_inicial}'
                })
            
            # Si hay pujas, la cantidad debe ser mayor que la puja más alta
            elif max_cantidad > 0 and data['cantidad'] <= max_cantidad:
                raise serializers.ValidationError({
                    'cantidad': f'La cantidad debe ser mayor que la puja más alta actual: {max_cantidad}'
                })
            
        return data
        
class PujaDetailSerializer(serializers.ModelSerializer):
    subasta = SubastaSerializer(read_only=True)
    
    class Meta:
        model = Puja
        fields = '__all__'
