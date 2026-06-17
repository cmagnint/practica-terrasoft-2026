"""
URL configuration for campo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from cosecha.permissions import es_admin, es_supervisor, es_trabajador
from cosecha.serializers import SupervisorSerializer, TrabajadorSerializer


#vista que devuelve informacion del usuario autenticado
class MeView(APIView):

    #devuelve usuario, correo, rol y perfil asociado
    def get(self, request):

        user = request.user
        rol = 'sin_rol'
        perfil = None

        #detecta si el usuario pertenece al grupo admin
        if es_admin(user):
            rol = 'admin'

        #detecta si el usuario pertenece al grupo supervisor
        elif es_supervisor(user):
            rol = 'supervisor'

            if hasattr(user, 'supervisor'):
                perfil = SupervisorSerializer(user.supervisor).data

        #detecta si el usuario pertenece al grupo trabajador
        elif es_trabajador(user):
            rol = 'trabajador'

            if hasattr(user, 'trabajador'):
                perfil = TrabajadorSerializer(user.trabajador).data

        return Response({
            'username': user.username,
            'email': user.email,
            'rol': rol,
            'perfil': perfil
        })


urlpatterns = [
    #panel de administracion de django
    path('admin/', admin.site.urls),

    #rutas de autenticacion con jwt
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', MeView.as_view(), name='auth_me'),

    #rutas principales de la app cosecha
    path('api/', include('cosecha.urls')),

    #rutas de documentacion
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
