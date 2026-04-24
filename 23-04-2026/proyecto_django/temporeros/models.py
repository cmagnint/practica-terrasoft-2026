from django.db import models

class Temporero(models.Model):

	TALLAS = [
		('S',  'S'),('M', 'M'),('L', 'L'),('XL', 'XL'),
	]

	nombre = models.CharField(max_length=100)
	rut = models.CharField(max_length=12, unique=True)
	telefono = models.CharField(max_length=20, null=True, blank=True)
	telefono =  models.CharField(max_length=20, null=True, blank=True)
	contacto_emergencia = models.CharField(max_length=100, null=True, blank=True)
	fecha_ingreso = models.DateField()
	supervisor = models.BooleanField(default=False)
	fecha_nacimiento = models.DateField()
	talla_polera = models.CharField(max_length=2, choices=TALLAS)
	activo = models.BooleanField(default=True)

	def __str__(self):
		return self.nombre
