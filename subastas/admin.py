from django.contrib import admin
from .models import Subasta, Categoria, Puja, Rating, Comentario

# Registrar los modelos en el panel de administración de Django
# Esto permite gestionar estos modelos directamente desde la interfaz administrativa
admin.site.register(Subasta)
admin.site.register(Categoria)
admin.site.register(Puja)
admin.site.register(Rating)
admin.site.register(Comentario)
