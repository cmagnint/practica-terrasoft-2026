from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class Temporero(models.Model):

	TALLAS = [
		('S',  'S'),('M', 'M'),('L', 'L'),('XL', 'XL'),
	]

	nombre = models.CharField(max_length=100)
	rut = models.CharField(max_length=12, unique=True)
	telefono = models.CharField(max_length=20, null=True, blank=True)
	contacto_emergencia = models.CharField(max_length=100, null=True, blank=True)
	fecha_ingreso = models.DateField()
	supervisor = models.BooleanField(default=False)
	fecha_nacimiento = models.DateField()
	talla_polera = models.CharField(max_length=2, choices=TALLAS)
	activo = models.BooleanField(default=True)

	def __str__(self):
		return self.nombre

class Cuartel(models.Model):
    VARIEDADES = [
        ('Duke', 'Duke'),
        ('Legacy', 'Legacy'),
        ('Brigitta', 'Brigitta'),
        ('Star', 'Star'),
    ]

    nombre = models.CharField(max_length=50, unique=True)
    hectareas = models.DecimalField(max_digits=6, decimal_places=2)
    variedad = models.CharField(max_length=50, choices=VARIEDADES)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Cuartel {self.nombre} - {self.variedad}"

class Labor(models.Model):
    TIPOS = [
        ('Poda', 'Poda'),
        ('Cosecha', 'Cosecha'),
        ('Riego', 'Riego'),
        ('Pesticida', 'Pesticida'),
        ('Limpieza', 'Limpieza'),
    ]

    temporero = models.ForeignKey(
        Temporero,
        on_delete=models.PROTECT,
        related_name='labores'
    )

    cuartel = models.ForeignKey(
        Cuartel,
        on_delete=models.PROTECT,
        related_name='labores'
    )

    tipo = models.CharField(max_length=30, choices=TIPOS)
    fecha = models.DateField()
    horas_trabajadas = models.DecimalField(max_digits=4, decimal_places=2)
    kilos_cosechados = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.temporero.nombre} - {self.tipo} en {self.cuartel.nombre} ({self.fecha})"

    def clean(self):
        if self.horas_trabajadas < 0 or self.horas_trabajadas > 12:
            raise ValidationError("Las horas trabajadas deben estar entre 0 y 12")

        if self.tipo == 'Cosecha' and self.kilos_cosechados is None:
            raise ValidationError("Debe ingresar kilos cosechados para labores de cosecha")

        if self.tipo != 'Cosecha' and self.kilos_cosechados is not None:
            raise ValidationError("Solo la cosecha puede tener kilos cosechados")

        if self.fecha > now().date():
            raise ValidationError("La fecha no puede ser futura")

        if self.fecha < self.temporero.fecha_ingreso:
            raise ValidationError("La fecha no puede ser anterior al ingreso del temporero")

    def save(self, *args, **kwargs):
    	self.full_clean()
    	super().save(*args, **kwargs)

    class Meta:
        ordering = ['-fecha', 'temporero__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['temporero', 'cuartel', 'tipo', 'fecha'],
                name='unique_labor_por_dia'
            )
        ]
