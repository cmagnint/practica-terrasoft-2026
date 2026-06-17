from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


#modelo que representa a un supervisor del huerto
class Supervisor(models.Model):

    #datos principales del supervisor
    nombre = models.CharField(max_length=120)
    rut = models.CharField(max_length=12, unique=True)
    zona = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    #relacion uno a uno con el usuario de django
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervisor'
    )

    #configuracion del modelo
    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['rut']),
            models.Index(fields=['activo']),
        ]

    #representacion legible del supervisor
    def __str__(self):
        return f'{self.nombre} - {self.rut}'


#modelo que representa a un trabajador o cosechero
class Trabajador(models.Model):

    #datos principales del trabajador
    nombre = models.CharField(max_length=120)
    rut = models.CharField(max_length=12, unique=True)
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)

    #relacion con el supervisor encargado de su cuadrilla
    supervisor = models.ForeignKey(
        Supervisor,
        on_delete=models.PROTECT,
        related_name='trabajadores'
    )

    #relacion opcional con el usuario de django
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trabajador'
    )

    #configuracion del modelo
    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['rut']),
            models.Index(fields=['activo']),
            models.Index(fields=['supervisor']),
        ]

    #representacion legible del trabajador
    def __str__(self):
        return f'{self.nombre} - {self.rut}'


#modelo que representa un cuartel del huerto
class Cuartel(models.Model):

    #opciones permitidas para la variedad del cuartel
    VARIEDAD_DUKE = 'Duke'
    VARIEDAD_LEGACY = 'Legacy'
    VARIEDAD_BRIGITTA = 'Brigitta'
    VARIEDAD_LIBERTY = 'Liberty'

    VARIEDADES = [
        (VARIEDAD_DUKE, 'Duke'),
        (VARIEDAD_LEGACY, 'Legacy'),
        (VARIEDAD_BRIGITTA, 'Brigitta'),
        (VARIEDAD_LIBERTY, 'Liberty'),
    ]

    #datos principales del cuartel
    nombre = models.CharField(max_length=80, unique=True)
    hectareas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    variedad = models.CharField(max_length=20, choices=VARIEDADES)
    activo = models.BooleanField(default=True)

    #relacion con el supervisor encargado del cuartel
    supervisor = models.ForeignKey(
        Supervisor,
        on_delete=models.PROTECT,
        related_name='cuarteles'
    )

    #configuracion del modelo
    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
            models.Index(fields=['supervisor']),
        ]

    #representacion legible del cuartel
    def __str__(self):
        return f'{self.nombre} - {self.variedad}'


#modelo que representa un registro diario de cosecha
class RegistroCosecha(models.Model):

    #opciones permitidas para la calidad de la cosecha
    CALIDAD_EXPORTACION = 'Exportacion'
    CALIDAD_NACIONAL = 'Nacional'
    CALIDAD_DESCARTE = 'Descarte'

    CALIDADES = [
        (CALIDAD_EXPORTACION, 'Exportacion'),
        (CALIDAD_NACIONAL, 'Nacional'),
        (CALIDAD_DESCARTE, 'Descarte'),
    ]

    #trabajador que realizo la cosecha
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='registros'
    )

    #cuartel donde se realizo la cosecha
    cuartel = models.ForeignKey(
        Cuartel,
        on_delete=models.PROTECT,
        related_name='registros'
    )

    #datos principales del registro
    fecha = models.DateField()

    kilos = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    horas = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0.01),
            MaxValueValidator(12)
        ]
    )

    calidad = models.CharField(max_length=20, choices=CALIDADES)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    #configuracion del modelo
    class Meta:
        ordering = ['-fecha', '-creado_en']
        constraints = [
            models.UniqueConstraint(
                fields=['trabajador', 'cuartel', 'fecha'],
                name='unique_registro_trabajador_cuartel_fecha'
            )
        ]
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['calidad']),
            models.Index(fields=['trabajador']),
            models.Index(fields=['cuartel']),
        ]

    #representacion legible del registro
    def __str__(self):
        return f'{self.trabajador.nombre} - {self.cuartel.nombre} - {self.fecha}'


#modelo que guarda acciones importantes realizadas en el sistema
class AuditLog(models.Model):

    #usuario que realizo la accion auditada
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias'
    )

    #datos generales de la accion
    accion = models.CharField(max_length=80)
    modelo = models.CharField(max_length=80)
    objeto_id = models.CharField(max_length=80)
    descripcion = models.TextField(blank=True)

    #datos antes y despues del cambio
    datos_previos = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)

    #fecha y hora en que se registro la accion
    timestamp = models.DateTimeField(auto_now_add=True)

    #configuracion del modelo
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['accion']),
            models.Index(fields=['modelo']),
            models.Index(fields=['timestamp']),
        ]

    #representacion legible de la auditoria
    def __str__(self):
        return f'{self.accion} - {self.modelo} - {self.objeto_id}'
