from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser
from .serializers import UserSerializer, ChangePasswordSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador personalizado para obtener tokens JWT.
    
    Extiende el serializador estándar para incluir el nombre de usuario
    en la respuesta junto con los tokens.
    """
    def validate(self, attrs):
        """
        Sobrescribe el método validate para agregar el nombre de usuario a la respuesta.
        """
        data = super().validate(attrs)
        data['username'] = self.user.username
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT.
    
    Utiliza el serializador personalizado que incluye el nombre de usuario en la respuesta.
    """
    serializer_class = CustomTokenObtainPairSerializer

class UserRegisterView(generics.CreateAPIView):
    """
    Vista para registrar un nuevo usuario.
    
    POST: Crea un nuevo usuario y devuelve los tokens de autenticación.
    
    No requiere autenticación para acceder.
    """
    permission_classes = [AllowAny]  # Cualquiera puede registrarse
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo usuario y genera tokens JWT para él.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Genera tokens para el usuario recién creado
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': serializer.data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListAPIView):
    """
    Vista para listar todos los usuarios.
    
    GET: Obtiene lista de todos los usuarios.
    
    Solo los administradores pueden acceder a esta vista.
    """
    permission_classes = [IsAdminUser]  # Solo administradores
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para gestionar usuarios específicos.
    
    GET: Obtiene detalles de un usuario específico
    PUT/PATCH: Actualiza un usuario específico
    DELETE: Elimina un usuario específico
    
    Solo los administradores pueden acceder a esta vista.
    """
    permission_classes = [IsAdminUser]  # Solo administradores
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()

class LogoutView(APIView):
    """
    Vista para cerrar sesión de un usuario.
    
    POST: Recibe el token de refresco y lo añade a la lista negra,
    invalidando así tanto el token de acceso como el de refresco.
    
    Requiere autenticación para acceder.
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def post(self, request):
        """
        Añade el token de refresco a la lista negra para invalidarlo.
        """
        try:
            refresh_token = request.data.get('refresh', None)
            if not refresh_token:
                return Response({"detail": "No refresh token provided."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Invalidar el token añadiéndolo a la lista negra
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    """
    Vista para gestionar el perfil del usuario autenticado.
    
    GET: Obtiene los datos del perfil del usuario actual
    PATCH: Actualiza parcialmente los datos del perfil del usuario actual
    DELETE: Elimina la cuenta del usuario actual
    
    Requiere autenticación para acceder.
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request):
        """
        Obtiene los datos del perfil del usuario autenticado.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """
        Actualiza parcialmente los datos del perfil del usuario autenticado.
        """
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """
        Elimina la cuenta del usuario autenticado.
        """
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChangePasswordView(APIView):
    """
    Vista para cambiar la contraseña del usuario autenticado.
    
    POST: Recibe la contraseña actual y la nueva contraseña, verifica la actual
    y establece la nueva si cumple los requisitos de validación.
    
    Requiere autenticación para acceder.
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def post(self, request):
        """
        Cambia la contraseña del usuario autenticado.
        
        Valida que:
        - La contraseña actual sea correcta
        - La nueva contraseña cumpla con las políticas de seguridad de Django
        """
        serializer = ChangePasswordSerializer(data=request.data)
        user = request.user
        
        if serializer.is_valid():
            # Verificar que la contraseña actual sea correcta
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": "Incorrect current password."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar la nueva contraseña según las políticas de seguridad de Django
            try:
                validate_password(serializer.validated_data['new_password'], user)
            except ValidationError as e:
                error_messages = {}
                if len(e.messages) == 1 and 'similar' in e.messages[0].lower():
                    error_messages["new_password"] = "La contraseña es demasiado similar a tu nombre de usuario."
                else:
                    error_messages["new_password"] = e.messages
                return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
            
            # Establecer la nueva contraseña
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({"detail": "Password updated successfully."})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)