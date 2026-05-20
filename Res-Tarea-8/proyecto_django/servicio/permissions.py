from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):
    """Permitira el acceso solo a los admin"""

    def has_permission(self, request, view):

        #is staff indica administrador django y request user es usuario autenticado actual jwt
        return request.user.is_staff


class EsMecanico(BasePermission):
    """Permitira el acceso solo mecanicos"""

    def has_permission(self, request, view):

        #hasattr verifica si usuario tiene relacion mecanico
        return hasattr(
            request.user,
            'mecanico'
        )


class EsCliente(BasePermission):
    """Permite acceso solo clientes"""

    def has_permission(self, request, view):

        #hasattr verifica si usuario tiene relacion cliente
        return hasattr(
            request.user,
            'cliente'
        )

class EsAdministradorOMecanico(BasePermission):
    """Permite acceso administradores o mecanicos"""

    def has_permission(self, request, view):

        #is staff identifica administradores django
        es_admin = request.user.is_staff

        #hasattr verifica relacion mecanico
        es_mecanico = hasattr(
            request.user,
            'mecanico'
        )

        #or permite cualquiera de las dos condiciones
        return es_admin or es_mecanico
