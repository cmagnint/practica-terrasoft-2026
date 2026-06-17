from rest_framework.permissions import BasePermission


#verifica si el usuario pertenece al grupo admin
def es_admin(user):
    return user.groups.filter(name='admin').exists()


#verifica si el usuario pertenece al grupo supervisor
def es_supervisor(user):
    return user.groups.filter(name='supervisor').exists()


#verifica si el usuario pertenece al grupo trabajador
def es_trabajador(user):
    return user.groups.filter(name='trabajador').exists()


#permite acceso solo a administradores
class EsAdmin(BasePermission):

    def has_permission(self, request, view):
        return es_admin(request.user)


#permite acceso a administradores y supervisores
class EsAdminOSupervisor(BasePermission):

    def has_permission(self, request, view):
        return (
            es_admin(request.user)
            or es_supervisor(request.user)
        )


#permite acceso solo a trabajadores
class EsTrabajador(BasePermission):

    def has_permission(self, request, view):
        return es_trabajador(request.user)
