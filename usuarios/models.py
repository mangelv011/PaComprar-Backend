from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Modelo personalizado de usuario que extiende el modelo de usuario por defecto de Django.
    
    Agrega campos adicionales específicos para el sistema de subastas:
    - birth_date: Fecha de nacimiento del usuario
    - locality: Localidad donde reside el usuario
    - municipality: Municipio donde reside el usuario
    
    Hereda todas las funcionalidades del modelo AbstractUser de Django, incluyendo:
    username, password, email, first_name, last_name, is_staff, is_active, date_joined, etc.
    """
    birth_date = models.DateField()  # Fecha de nacimiento del usuario
    locality = models.CharField(max_length=100, blank=True)  # Localidad (opcional)
    municipality = models.CharField(max_length=100, blank=True)  # Municipio (opcional)
    
    def __str__(self):
        """Representación en texto del objeto usuario."""
        return self.username