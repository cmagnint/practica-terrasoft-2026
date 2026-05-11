from django.urls import path
from . import views


urlpatterns = [

    path('mecanicos/', views.MecanicoListView.as_view()),

    path('mecanicos/<str:rut>/', views.MecanicoDetailView.as_view()),

    path('clientes/', views.ClienteListView.as_view()),

    path('clientes/<str:rut>/', views.ClienteDetailView.as_view()),

    path('vehiculos/', views.VehiculoListView.as_view()),

    path('vehiculos/<str:patente>/', views.VehiculoDetailView.as_view()),

    path('ordenes/', views.OrdenTrabajoListCreateView.as_view()),

    path('ordenes/<int:pk>/', views.OrdenTrabajoDetailView.as_view()),

    path('estadisticas/', views.EstadisticasView.as_view()),
]
