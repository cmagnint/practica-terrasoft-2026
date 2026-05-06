from django.urls import path
from . import views  #importa las views de temporeros/views.py?

urlpatterns = [
    #la ruta: /api/temporeros/
    path('temporeros/', views.TemporeroListView.as_view()),
    path('temporeros/<str:rut>/', views.TemporeroDetailView.as_view()),

    path('cuarteles/', views.CuartelListView.as_view()),
    path('cuarteles/<str:nombre>/', views.CuartelDetailView.as_view()),

    path('labores/', views.LaborView.as_view()),

    path('resumen/', views.ResumenView.as_view()),
]
