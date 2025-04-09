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
]
