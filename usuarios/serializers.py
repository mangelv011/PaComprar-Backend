from rest_framework import serializers
from .models import CustomUser
import re

class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'birth_date', 
                  'municipality', 'locality', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        user = self.instance  # Solo tiene valor cuando se está actualizando
        if CustomUser.objects.filter(email=value).exclude(
                pk=user.pk if user else None).exists():
            raise serializers.ValidationError("Email already in use.")
        return value

    def validate_password(self, value):
        # Verificar longitud mínima
        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )
        
        # Verificar que contenga letras y números
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise serializers.ValidationError(
                "La contraseña debe contener letras y números."
            )
        
        return value
    
    def validate(self, data):
        # Si estamos en un contexto de actualización y se incluye password2
        if 'password' in data and 'password2' in data:
            if data['password'] != data['password2']:
                raise serializers.ValidationError({
                    "password": "Las contraseñas no coinciden."
                })
            # Eliminar password2 para no intentar guardarlo
            data.pop('password2')
        return data

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        # Manejar la contraseña de forma especial
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        
        # Actualizar todos los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        # Verificar longitud mínima
        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )
        
        # Verificar que contenga letras y números
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise serializers.ValidationError(
                "La contraseña debe contener letras y números."
            )
        
        return value