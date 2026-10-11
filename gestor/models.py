from django.db import models


class Predio(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField("ubicación", max_length=200)
    superficie_hectareas = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.nombre


class Cuartel(models.Model):
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class LecturaSensor(models.Model):
    cuartel = models.ForeignKey(Cuartel, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    telemetria_dinamica = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.cuartel} · {self.fecha:%d/%m/%Y %H:%M}"