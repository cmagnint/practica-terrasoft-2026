from .models import AuditLog

def registrar_auditoria(
    usuario,
    accion,
    modelo,
    descripcion,
    objeto_id=None,
    datos_previos=None,
    datos_nuevos=None
):
    """Registra cada accion importante en el sistema"""

    #create inserta registro nuevo bd
    AuditLog.objects.create(

        #usuario autenticado realizo una accion
        usuario=usuario,

        #accion, ej completar orden
        accion=accion,

        #modelo afectado, ejemplo OrdenTrabajo
        modelo=modelo,

        #id objeto afectado
        objeto_id=objeto_id,

        #descripcion legible al usuario
        descripcion=descripcion,

        #estado json antes del cambio
        datos_previos=datos_previos,

        #estado json despues del cambio
        datos_nuevos=datos_nuevos
    )
