from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User, Group


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

class Administrador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

    def __str__(self):
        return self.user.username

class Trabajador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"

    def __str__(self):
        return self.user.username

class JCuadrilla(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Jefe de Cuadrilla"
        verbose_name_plural = "Jefes de Cuadrilla"

    def __str__(self):
        return self.user.username