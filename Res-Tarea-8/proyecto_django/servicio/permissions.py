from rest_framework.permissions import BasePermission


def es_admin(user):
    """Verifica si el usuario pertenece al grupo admin"""

    return (
        user.is_authenticated
        and (
            user.is_superuser
            or
            user.groups.filter(name='admin').exists()
        )
    )


def es_mecanico(user):
    """Verifica si el usuario pertenece al grupo mecanico"""

    return (
        user.is_authenticated
        and
        user.groups.filter(name='mecanico').exists()
    )


def es_cliente(user):
    """Verifica si el usuario pertenece al grupo cliente"""

    return (
        user.is_authenticated
        and
        user.groups.filter(name='cliente').exists()
    )


class EsAdministrador(BasePermission):
    """Permite acceso solo administradores"""

    def has_permission(self, request, view):

        return es_admin(request.user)


class EsMecanico(BasePermission):
    """Permite acceso solo mecanicos"""

    def has_permission(self, request, view):

        return es_mecanico(request.user)


class EsCliente(BasePermission):
    """Permite acceso solo clientes"""

    def has_permission(self, request, view):

        return es_cliente(request.user)


class EsAdministradorOMecanico(BasePermission):
    """Permite acceso administradores o mecanicos"""

    def has_permission(self, request, view):

        return (
            es_admin(request.user)
            or
            es_mecanico(request.user)
        )
