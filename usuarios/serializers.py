from rest_framework import serializers
from .models import CustomUser
import re

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo CustomUser.
    
    Maneja la serialización de los datos de usuario incluyendo validación de contraseñas
    y campos requeridos. Proporciona métodos para crear y actualizar usuarios con manejo
    seguro de contraseñas.
    """
    # Campo adicional para confirmar contraseña (solo para escritura)
    password2 = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'birth_date', 
                  'municipality', 'locality', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True},  # La contraseña no se devuelve en las respuestas
            'first_name': {'required': True},  # Nombre es obligatorio
            'last_name': {'required': True},   # Apellido es obligatorio
        }

    def validate_email(self, value):
        """
        Valida que el email no esté ya en uso por otro usuario.
        En caso de actualización, excluye el usuario actual de la comprobación.
        """
        user = self.instance
        if CustomUser.objects.filter(email=value).exclude(pk=user.pk if user else None).exists():
            raise serializers.ValidationError("Email already in use.")
        return value

    def validate_password(self, value):
        """
        Valida que la contraseña cumpla con los requisitos mínimos:
        - Al menos 8 caracteres
        - Debe contener letras y números
        """
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise serializers.ValidationError("La contraseña debe contener letras y números.")
        return value
    
    def validate(self, data):
        """
        Valida que las contraseñas coincidan cuando se proporcionan ambas.
        Elimina password2 de los datos validados ya que no es un campo del modelo.
        """
        if 'password' in data and 'password2' in data:
            if data['password'] != data['password2']:
                raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
            data.pop('password2')
        return data

    def create(self, validated_data):
        """
        Crea un nuevo usuario utilizando el método create_user que hashea la contraseña.
        """
        return CustomUser.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Actualiza un usuario existente.
        Si se proporciona una contraseña, la hashea antes de guardarla.
        """
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        
        # Actualiza todos los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializador para cambiar la contraseña de un usuario.
    
    Requiere la contraseña actual (old_password) y la nueva contraseña (new_password).
    La verificación de que la contraseña actual sea correcta se realiza en la vista.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        """
        Valida que la nueva contraseña cumpla con los requisitos mínimos:
        - Al menos 8 caracteres
        - Debe contener letras y números
        """
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise serializers.ValidationError("La contraseña debe contener letras y números.")
        return value