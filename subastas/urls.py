from django.urls import path
from . import views

app_name = "subastas"
urlpatterns = [
    # Subastas (Auctions)
    path('subastas/', views.SubastaListCreate.as_view(), name='subastas_list'),  # GET, POST
    path('subastas/<int:id_subasta>/', views.SubastaRetrieveUpdateDestroy.as_view(), name='subasta_detail'),  # GET, PUT, DELETE
    
    # URLs para usuarios (solicitud específica)
    path('misSubastas/', views.UserSubastaListView.as_view(), name='mis_subastas'),  # GET
    path('misPujas/', views.UserPujaListView.as_view(), name='mis_pujas'),  # GET
    path('misValoraciones/', views.UserRatingListView.as_view(), name='mis_valoraciones'),  # GET
    path('misComentarios/', views.UserComentarioListView.as_view(), name='mis_comentarios'),  # GET
    
    # Rutas alternativas (mantener para compatibilidad)
    path('usuario/subastas/', views.UserSubastaListView.as_view(), name='user_subastas'),  # GET
    path('users/', views.UserSubastaListView.as_view(), name='action-from-users'),  # GET
    
    # Categorías (Categories)
    path('subastas/categorias/', views.CategoriaListCreate.as_view(), name='categorias_list'),  # GET, POST
    path('subastas/categoria/<int:id_categoria>/', views.CategoriaRetrieve.as_view(), name='categoria_detail'),  # GET
    path('subasta/categoria/<int:id_categoria>/', views.CategoriaUpdateDestroy.as_view(), name='categoria_update_delete'),  # PUT, DELETE
    
    # Pujas (Bids)
    path('subastas/<int:id_subasta>/pujas/', views.PujaListCreate.as_view(), name='pujas_list'),  # GET, POST
    path('subastas/<int:id_subasta>/pujas/<int:idPuja>/', views.PujaRetrieveUpdateDestroy.as_view(), name='puja_detail'),  # GET, PUT, DELETE
    
    # Valoraciones (Ratings)
    path('subastas/<int:id_subasta>/ratings/', views.RatingListCreate.as_view(), name='ratings_list'),  # GET, POST
    path('subastas/<int:id_subasta>/ratings/<int:id_rating>/', views.RatingDetailView.as_view(), name='rating_detail'),  # GET, PUT, DELETE
    path('subastas/<int:id_subasta>/mi-rating/', views.UserRatingView.as_view(), name='mi_rating'),  # GET, DELETE
    
    # Comentarios (Comments)
    path('subastas/<int:id_subasta>/comentarios/', views.ComentarioListCreate.as_view(), name='comentarios_list'),  # GET, POST
    path('subastas/<int:id_subasta>/comentarios/<int:id_comentario>/', views.ComentarioDetailView.as_view(), name='comentario_detail'),  # GET, PUT, DELETE
]
