from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Registrar el modelo CustomUser con la configuración de UserAdmin
# Esto permite gestionar usuarios desde el panel de administración con todas las funcionalidades
admin.site.register(CustomUser, UserAdmin)
