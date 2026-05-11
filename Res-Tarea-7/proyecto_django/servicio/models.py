# Create your models here.

from django.db import models


class Mecanico(models.Model):
#Representa a un mecanico del taller

    #esto limita las elecciones que tendra "choices" en el siguiente bloque
    ESPECIALIDADES = [
        ('Motor', 'Motor'),
        ('Electricidad', 'Electricidad'),
        ('Carrocería', 'Carrocería'),
        ('Frenos', 'Frenos'),
        ('General', 'General'),
    ]

    nombre = models.CharField(max_length=100)

    #para impedir que hayan 2 mecanicos con el mismo rut, se utiliza unique=True
    rut = models.CharField(max_length=12, unique=True)

    especialidad = models.CharField(
        max_length=30,
        choices=ESPECIALIDADES
    )

    #este bloque hace que cuando se agregue un nuevo mecanico, quede marcado como activo
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.especialidad})"


class Cliente(models.Model):
    """Representa a un cliente dueño de uno o más vehículos"""

    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)

    #blank=True permite dejar el campo vacio en formularios/API
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)

    #auto_now_add=True guarda automaticamente la fecha de creacion
    fecha_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


class Vehiculo(models.Model):
    """Representa un vehículo perteneciente a un cliente."""

    patente = models.CharField(max_length=8, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.IntegerField()
    color = models.CharField(max_length=30)

    #si no se encuentra algun valor, el kilometraje del
    kilometraje = models.IntegerField(default=0)

    # Relación: un cliente puede tener muchos vehículos.
    cliente = models.ForeignKey(
        Cliente,

        # PROTECT evita borrar un cliente si tiene vehículos asociados.
        on_delete=models.PROTECT,

        #aca permite acceder desde cliente hacia sus vehiculos=cliente.vehiculos.all()
        related_name='vehiculos'
    )

    def __str__(self):
        return f"{self.patente} — {self.marca} {self.modelo} ({self.anio})"


class OrdenTrabajo(models.Model):
    """Representa una orden de trabajo asociada a un vehículo y mecánico."""

    #estados permitidos para una orden.
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En progreso', 'En progreso'),
        ('Completada', 'Completada'),
        ('Cancelada', 'Cancelada'),
    ]

    #relacion= una orden pertenece a un vehiculo
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,

        #permite acceder desde vehiculo hacia sus ordenes=vehiculo.ordenes.all()
        related_name='ordenes'
    )

    #relacion= una orden es asignada a un mecanico
    mecanico = models.ForeignKey(
        Mecanico,
        on_delete=models.PROTECT,

        #permite acceder desde mecanico hacia sus ordenes=mecanico.ordenes.all()
        related_name='ordenes'
    )

    descripcion = models.TextField()

    #toda orden nueva parte como pendiente
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Pendiente'
    )

    #fecha automática cuando se crea la orden
    fecha_ingreso = models.DateField(auto_now_add=True)

    fecha_entrega_estimada = models.DateField()

    #null=True permite NULL en la base de datos
    #blank=True permite dejar vacío desde formularios
    fecha_entrega_real = models.DateField(null=True, blank=True)

    #DecimalField se usa para dinero, no FloatField
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Orden #{self.pk} — {self.vehiculo.patente} ({self.estado})"

    class Meta:
        #ordena por fecha de ingreso descendente, las ordenes más recientes aparecen primero
        ordering = ['-fecha_ingreso']
