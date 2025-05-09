from rest_framework import serializers
from .models import Categoria, Subasta, Puja, Rating, Comentario
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max, Avg

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = ['id', 'valor', 'usuario', 'usuario_nombre', 'subasta', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_actualizacion', 'subasta']
    
    def get_usuario_nombre(self, obj):
        return obj.usuario.username
    
    def validate_valor(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La valoración debe estar entre 1 y 5")
        return value
    
    def create(self, validated_data):
        # Si la subasta está en el contexto, usarla
        if 'subasta' not in validated_data and 'subasta' in self.context:
            validated_data['subasta'] = self.context['subasta']
        return super().create(validated_data)

class ComentarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Comentario
        fields = ['id', 'titulo', 'texto', 'fecha_creacion', 'fecha_actualizacion', 
                 'usuario', 'usuario_nombre', 'subasta']
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_actualizacion', 'subasta']
    
    def get_usuario_nombre(self, obj):
        return obj.usuario.username
        
    def create(self, validated_data):
        # Si la subasta está en el contexto, usarla
        if 'subasta' not in validated_data and 'subasta' in self.context:
            validated_data['subasta'] = self.context['subasta']
        return super().create(validated_data)

class SubastaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    precio_actual = serializers.SerializerMethodField()
    valoracion_media = serializers.SerializerMethodField()
    
    class Meta:
        model = Subasta
        fields = '__all__'
        read_only_fields = ['estado', 'fecha_creacion', 'valoracion_media']
    
    def get_usuario_nombre(self, obj):
        return obj.usuario.username if obj.usuario else None
    
    def get_precio_actual(self, obj):
        # Obtener la puja más alta o el precio inicial si no hay pujas
        puja_mas_alta = obj.pujas.aggregate(max_cantidad=Max('cantidad'))
        max_cantidad = puja_mas_alta.get('max_cantidad')
        return max_cantidad if max_cantidad else obj.precio_inicial
    
    def get_valoracion_media(self, obj):
        """Devuelve la valoración media de la subasta"""
        return obj.get_valoracion_media()
    
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
    usuario_nombre = serializers.SerializerMethodField()
    precio_actual = serializers.SerializerMethodField()
    valoracion_media = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    comentarios = serializers.SerializerMethodField()
    
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
    
    def get_usuario_nombre(self, obj):
        return obj.usuario.username if obj.usuario else None
        
    def get_precio_actual(self, obj):
        # Obtener la puja más alta o el precio inicial si no hay pujas
        puja_mas_alta = obj.pujas.aggregate(max_cantidad=Max('cantidad'))
        max_cantidad = puja_mas_alta.get('max_cantidad')
        return max_cantidad if max_cantidad else obj.precio_inicial
    
    def get_valoracion_media(self, obj):
        """Devuelve la valoración media de la subasta"""
        return obj.get_valoracion_media()
    
    def get_ratings(self, obj):
        """Devuelve las valoraciones individuales de la subasta"""
        return RatingSerializer(obj.ratings.all(), many=True).data
    
    def get_comentarios(self, obj):
        """Devuelve los comentarios de la subasta"""
        return ComentarioSerializer(obj.comentarios.all(), many=True).data

class PujaSerializer(serializers.ModelSerializer):
    pujador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Puja
        fields = '__all__'
        read_only_fields = ['subasta', 'fecha_puja']
    
    def get_pujador_nombre(self, obj):
        return obj.pujador.username if obj.pujador else None
    
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
    pujador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Puja
        fields = '__all__'
    
    def get_pujador_nombre(self, obj):
        return obj.pujador.username if obj.pujador else None
