from rest_framework import serializers
from .models import Categoria, Subasta, Puja, Rating, Comentario
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max

class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Categoria.
    
    Expone todos los campos del modelo sin procesamiento adicional.
    """
    class Meta:
        model = Categoria
        fields = '__all__'  # Incluir todos los campos del modelo

class RatingSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Rating (valoración).
    
    Incluye campos calculados como el nombre del usuario que creó la valoración.
    """
    # Campo calculado con el nombre del usuario (para mostrar en la API)
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = ['id', 'valor', 'usuario', 'usuario_nombre', 'subasta', 'fecha_creacion', 'fecha_actualizacion']
        # Estos campos solo se pueden leer, no modificar en la API
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_actualizacion', 'subasta']
    
    def get_usuario_nombre(self, obj):
        """Obtiene el nombre de usuario del autor de la valoración."""
        return obj.usuario.username
    
    def validate_valor(self, value):
        """
        Valida que el valor de la valoración esté en el rango correcto (1-5).
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("La valoración debe estar entre 1 y 5")
        return value
    
    def create(self, validated_data):
        """
        Sobrescribe el método create para asignar la subasta desde el contexto si no está
        en los datos validados pero sí en el contexto.
        """
        if 'subasta' not in validated_data and 'subasta' in self.context:
            validated_data['subasta'] = self.context['subasta']
        return super().create(validated_data)

class ComentarioSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Comentario.
    
    Incluye campos calculados como el nombre del usuario que creó el comentario.
    """
    # Campo calculado con el nombre del usuario (para mostrar en la API)
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Comentario
        fields = ['id', 'titulo', 'texto', 'fecha_creacion', 'fecha_actualizacion', 
                 'usuario', 'usuario_nombre', 'subasta']
        # Estos campos solo se pueden leer, no modificar en la API
        read_only_fields = ['usuario', 'fecha_creacion', 'fecha_actualizacion', 'subasta']
    
    def get_usuario_nombre(self, obj):
        """Obtiene el nombre de usuario del autor del comentario."""
        return obj.usuario.username
        
    def create(self, validated_data):
        """
        Sobrescribe el método create para asignar la subasta desde el contexto si no está
        en los datos validados pero sí en el contexto.
        """
        if 'subasta' not in validated_data and 'subasta' in self.context:
            validated_data['subasta'] = self.context['subasta']
        return super().create(validated_data)

class SubastaSerializer(serializers.ModelSerializer):
    """
    Serializador principal para el modelo Subasta.
    
    Incluye campos calculados como:
    - usuario_nombre: Nombre del creador de la subasta
    - precio_actual: Precio actual según las pujas realizadas
    - valoracion_media: Valoración media calculada de todos los ratings
    """
    # Campos calculados
    usuario_nombre = serializers.SerializerMethodField()
    precio_actual = serializers.SerializerMethodField()
    valoracion_media = serializers.SerializerMethodField()
    
    class Meta:
        model = Subasta
        fields = '__all__'  # Incluir todos los campos del modelo
        # Estos campos solo se pueden leer, no modificar en la API
        read_only_fields = ['estado', 'fecha_creacion', 'valoracion_media']
    
    def get_usuario_nombre(self, obj):
        """Obtiene el nombre del usuario creador de la subasta."""
        return obj.usuario.username if obj.usuario else None
    
    def get_precio_actual(self, obj):
        """
        Calcula el precio actual de la subasta.
        Si hay pujas, devuelve la cantidad de la puja más alta.
        Si no hay pujas, devuelve el precio inicial.
        """
        puja_mas_alta = obj.pujas.aggregate(max_cantidad=Max('cantidad'))
        max_cantidad = puja_mas_alta.get('max_cantidad')
        return max_cantidad if max_cantidad else obj.precio_inicial
    
    def get_valoracion_media(self, obj):
        """Obtiene la valoración media de la subasta."""
        return obj.get_valoracion_media()
    
    def validate(self, data):
        """
        Valida los datos de la subasta:
        - Fecha de cierre en el futuro y al menos 15 días después
        - Precio inicial positivo
        - Stock al menos 1
        - Valoración entre 1 y 5
        """
        # Validar que la fecha de cierre sea futura
        if 'fecha_cierre' in data and data['fecha_cierre'] <= timezone.now():
            raise serializers.ValidationError({'fecha_cierre': 'La fecha de cierre debe ser posterior a la fecha actual'})
        
        # Validar que la fecha de cierre sea al menos 15 días después
        min_fecha_cierre = timezone.now() + timedelta(days=15)
        if 'fecha_cierre' in data and data['fecha_cierre'] < min_fecha_cierre:
            raise serializers.ValidationError({'fecha_cierre': 'La fecha de cierre debe ser al menos 15 días después de la fecha actual'})
        
        # Validar precio inicial positivo
        if 'precio_inicial' in data and data['precio_inicial'] <= 0:
            raise serializers.ValidationError({'precio_inicial': 'El precio debe ser mayor que 0'})
        
        # Validar stock positivo
        if 'stock' in data and data['stock'] <= 0:
            raise serializers.ValidationError({'stock': 'El stock debe ser al menos 1'})
        
        # Validar valoración en rango correcto
        if 'valoracion' in data and (data['valoracion'] < 1 or data['valoracion'] > 5):
            raise serializers.ValidationError({'valoracion': 'La valoración debe estar entre 1 y 5'})
        
        return data

class SubastaDetailSerializer(serializers.ModelSerializer):
    """
    Serializador detallado para el modelo Subasta.
    
    Amplía el serializador base agregando información relacionada como:
    - Pujas asociadas a la subasta
    - Nombre de la categoría
    - Estado actualizado (abierta/cerrada)
    - Valoraciones (ratings) asociadas
    - Comentarios asociados
    
    Se utiliza para mostrar la vista detallada de una subasta individual.
    """
    # Campos calculados con información relacionada
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
        fields = '__all__'  # Incluir todos los campos del modelo
        
    def get_pujas(self, obj):
        """Obtiene todas las pujas de la subasta ordenadas por cantidad descendente."""
        pujas = obj.pujas.all().order_by('-cantidad')
        return PujaSerializer(pujas, many=True).data
    
    def get_categoria_nombre(self, obj):
        """Obtiene el nombre de la categoría de la subasta."""
        return obj.categoria.nombre
    
    def get_estado_actual(self, obj):
        """
        Calcula el estado actual de la subasta.
        Si la fecha de cierre ha pasado, devuelve 'cerrada', de lo contrario 'abierta'.
        """
        return 'cerrada' if obj.fecha_cierre <= timezone.now() else 'abierta'
    
    def get_usuario_nombre(self, obj):
        """Obtiene el nombre del usuario creador de la subasta."""
        return obj.usuario.username if obj.usuario else None
        
    def get_precio_actual(self, obj):
        """
        Calcula el precio actual de la subasta.
        Si hay pujas, devuelve la cantidad de la puja más alta.
        Si no hay pujas, devuelve el precio inicial.
        """
        puja_mas_alta = obj.pujas.aggregate(max_cantidad=Max('cantidad'))
        max_cantidad = puja_mas_alta.get('max_cantidad')
        return max_cantidad if max_cantidad else obj.precio_inicial
    
    def get_valoracion_media(self, obj):
        """Obtiene la valoración media de la subasta."""
        return obj.get_valoracion_media()
    
    def get_ratings(self, obj):
        """Obtiene todas las valoraciones asociadas a la subasta."""
        return RatingSerializer(obj.ratings.all(), many=True).data
    
    def get_comentarios(self, obj):
        """Obtiene todos los comentarios asociados a la subasta."""
        return ComentarioSerializer(obj.comentarios.all(), many=True).data

class PujaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Puja.
    
    Incluye campos calculados como el nombre del pujador y realiza validaciones
    adicionales para asegurar que las pujas cumplen con las reglas de negocio.
    """
    # Campo calculado con el nombre del pujador (para mostrar en la API)
    pujador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Puja
        fields = '__all__'  # Incluir todos los campos del modelo
        # Estos campos solo se pueden leer, no modificar en la API
        read_only_fields = ['subasta', 'fecha_puja']
    
    def get_pujador_nombre(self, obj):
        """Obtiene el nombre del usuario que realizó la puja."""
        return obj.pujador.username if obj.pujador else None
    
    def validate(self, data):
        """
        Valida los datos de la puja con varias reglas de negocio:
        - Verifica que la subasta no esté cerrada al actualizar
        - Verifica que la cantidad sea positiva
        - Verifica que la cantidad supere el precio inicial o la puja más alta actual
        """
        # Al actualizar, verificar que la subasta esté abierta
        request = self.context.get('request')
        if request and request.method == 'PUT':
            subasta = self.instance.subasta
            if subasta.fecha_cierre <= timezone.now() or subasta.estado == 'cerrada':
                raise serializers.ValidationError("No se puede actualizar la puja en una subasta cerrada")
        
        # Validar cantidad positiva
        if 'cantidad' in data and data['cantidad'] <= 0:
            raise serializers.ValidationError({'cantidad': 'La cantidad de la puja debe ser mayor que 0'})
        
        # Validar que la cantidad sea mayor que la puja más alta o el precio inicial
        if self.context.get('subasta') and 'cantidad' in data:
            subasta = self.context.get('subasta')
            puja_mas_alta = subasta.pujas.aggregate(max_cantidad=Max('cantidad'))
            max_cantidad = puja_mas_alta.get('max_cantidad') if puja_mas_alta.get('max_cantidad') else 0
            
            # Si no hay pujas previas, comparar con el precio inicial
            if max_cantidad == 0 and data['cantidad'] < subasta.precio_inicial:
                raise serializers.ValidationError({'cantidad': f'La cantidad debe ser al menos igual al precio inicial: {subasta.precio_inicial}'})
            # Si hay pujas previas, comparar con la más alta
            elif max_cantidad > 0 and data['cantidad'] <= max_cantidad:
                raise serializers.ValidationError({'cantidad': f'La cantidad debe ser mayor que la puja más alta actual: {max_cantidad}'})
        
        return data

class PujaDetailSerializer(serializers.ModelSerializer):
    """
    Serializador detallado para el modelo Puja.
    
    Amplía el serializador base incluyendo información detallada de la subasta
    asociada y el nombre del pujador.
    """
    # Incluir la subasta completa en lugar de solo su ID
    subasta = SubastaSerializer(read_only=True)
    # Campo calculado con el nombre del pujador
    pujador_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Puja
        fields = '__all__'  # Incluir todos los campos del modelo
    
    def get_pujador_nombre(self, obj):
        """Obtiene el nombre del usuario que realizó la puja."""
        return obj.pujador.username if obj.pujador else None
