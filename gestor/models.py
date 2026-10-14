from django.db import models
from decimal import Decimal

class Predio(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField("ubicación", max_length=200)
    superficie_hectareas = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Predio"
        verbose_name_plural = "Predios"

    def __str__(self):
        return self.nombre


class Cuartel(models.Model):
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Cuartel"
        verbose_name_plural = "Cuarteles"

    def __str__(self):
        return self.nombre


class LecturaSensor(models.Model):
    cuartel = models.ForeignKey(Cuartel, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    telemetria_dinamica = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Lectura del Sensor"
        verbose_name_plural = "Lecturas del Sensor"

    def __str__(self):
        return f"{self.cuartel} · {self.fecha:%d/%m/%Y %H:%M}"