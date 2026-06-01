"""
URL configuration for taller project.

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
from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from servicio.views import MeView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [

    #panel admin django
    path('admin/', admin.site.urls),

    #rutas api
    path('api/', include('servicio.urls')),

    #login jwt
    path(
        'api/auth/login/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    #refresh token jwt
    path(
        'api/auth/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    #verify token jwt
    path(
        'api/auth/verify/',
        TokenVerifyView.as_view(),
        name='token_verify'
    ),

    #auth me devuelve usuario autenticado actual
    path(
        'api/auth/me/',
        MeView.as_view(),
        name='auth-me'
    ),

    #schema openapi formato json
    path(
        'api/schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),

    #swagger ui documentacion interactiva api
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema'
        ),
        name='swagger-ui'
    ),

    #redoc documentacion alternativa
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(
            url_name='schema'
        ),
        name='redoc'
    ),

]

#esto devuelve errores json en vez de html, cuando hayan rutas inexistentes
def handler_404(request, exception):

    return JsonResponse({

        "error": f"Recurso no encontrado: {request.path}"

    }, status=404)


handler404 = "taller.urls.handler_404"
