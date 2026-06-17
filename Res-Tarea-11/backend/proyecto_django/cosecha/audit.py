from .models import AuditLog


#registra una accion en la tabla de auditoria
def registrar_auditoria(
    usuario,
    accion,
    modelo,
    objeto_id,
    descripcion='',
    datos_previos=None,
    datos_nuevos=None
):

    AuditLog.objects.create(
        usuario=usuario,
        accion=accion,
        modelo=modelo,
        objeto_id=str(objeto_id),
        descripcion=descripcion,
        datos_previos=datos_previos,
        datos_nuevos=datos_nuevos,
    )
