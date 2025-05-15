from django.urls import path
from . import views

app_name = "subastas"
urlpatterns = [
    # SUBASTAS
    # Listado general y creación de subastas
    path('subastas/', views.SubastaListCreate.as_view(), name='subastas_list'),
    # Detalles, actualización y eliminación de una subasta específica
    path('subastas/<int:id_subasta>/', views.SubastaRetrieveUpdateDestroy.as_view(), name='subasta_detail'),
    
    # ENDPOINTS ESPECÍFICOS DE USUARIO
    # Listado de subastas creadas por el usuario autenticado
    path('misSubastas/', views.UserSubastaListView.as_view(), name='mis_subastas'),
    # Listado de pujas realizadas por el usuario autenticado
    path('misPujas/', views.UserPujaListView.as_view(), name='mis_pujas'),
    # Listado de valoraciones hechas por el usuario autenticado
    path('misValoraciones/', views.UserRatingListView.as_view(), name='mis_valoraciones'),
    # Listado de comentarios hechos por el usuario autenticado
    path('misComentarios/', views.UserComentarioListView.as_view(), name='mis_comentarios'),
    
    # RUTAS ALTERNATIVAS (alias adicionales para endpoints de usuario)
    path('usuario/subastas/', views.UserSubastaListView.as_view(), name='user_subastas'),
    path('users/', views.UserSubastaListView.as_view(), name='action-from-users'),
    
    # CATEGORÍAS
    # Listado general y creación de categorías
    path('subastas/categorias/', views.CategoriaListCreate.as_view(), name='categorias_list'),
    # Detalles de una categoría específica (solo lectura)
    path('subastas/categoria/<int:id_categoria>/', views.CategoriaRetrieve.as_view(), name='categoria_detail'),
    # Actualización y eliminación de una categoría específica
    path('subasta/categoria/<int:id_categoria>/', views.CategoriaUpdateDestroy.as_view(), name='categoria_update_delete'),
    
    # PUJAS
    # Listado y creación de pujas para una subasta específica
    path('subastas/<int:id_subasta>/pujas/', views.PujaListCreate.as_view(), name='pujas_list'),
    # Detalles, actualización y eliminación de una puja específica
    path('subastas/<int:id_subasta>/pujas/<int:idPuja>/', views.PujaRetrieveUpdateDestroy.as_view(), name='puja_detail'),
    
    # VALORACIONES (RATINGS)
    # Listado y creación de valoraciones para una subasta específica
    path('subastas/<int:id_subasta>/ratings/', views.RatingListCreate.as_view(), name='ratings_list'),
    # Detalles, actualización y eliminación de una valoración específica
    path('subastas/<int:id_subasta>/ratings/<int:id_rating>/', views.RatingDetailView.as_view(), name='rating_detail'),
    # Obtener, crear o actualizar la valoración del usuario autenticado para una subasta específica
    path('subastas/<int:id_subasta>/mi-rating/', views.UserRatingView.as_view(), name='mi_rating'),
    
    # COMENTARIOS
    # Listado y creación de comentarios para una subasta específica
    path('subastas/<int:id_subasta>/comentarios/', views.ComentarioListCreate.as_view(), name='comentarios_list'),
    # Detalles, actualización y eliminación de un comentario específico
    path('subastas/<int:id_subasta>/comentarios/<int:id_comentario>/', views.ComentarioDetailView.as_view(), name='comentario_detail'),
]
