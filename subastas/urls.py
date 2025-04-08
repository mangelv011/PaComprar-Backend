from django.urls import path
from . import views

urlpatterns = [
    # Subastas (Auctions)
    path('subastas/', views.subastas_list, name='subastas_list'),  # GET, POST
    path('subastas/<int:id_subasta>/', views.subasta_detail, name='subasta_detail'),  # GET, PUT, DELETE
    
    # Categorías (Categories)
    path('subastas/categorias/', views.categorias_list, name='categorias_list'),  # GET, POST
    path('subastas/categoria/<int:id_categoria>/', views.categoria_detail, name='categoria_detail'),  # GET
    path('subasta/categoria/<int:id_categoria>/', views.categoria_update_delete, name='categoria_update_delete'),  # PUT, DELETE
    
    # Pujas (Bids)
    path('subastas/<int:id_subasta>/pujas/', views.pujas_list, name='pujas_list'),  # GET, POST
    path('subastas/<int:id_subasta>/pujas/<int:idPuja>/', views.puja_detail, name='puja_detail'),  # GET, PUT, DELETE
]
