from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


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


class Huerto(models.Model):
    predio = models.ForeignKey(
        Predio, on_delete=models.CASCADE, related_name="huertos"
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ["predio__nombre", "nombre"]
        verbose_name = "Huerto"
        verbose_name_plural = "Huertos"

    def __str__(self):
        return f"{self.predio.nombre} · {self.nombre}"


class Cuartel(models.Model):
    huerto = models.ForeignKey(
        Huerto, on_delete=models.CASCADE, related_name="cuarteles"
    )
    nombre = models.CharField(max_length=100)
    superficie_hectareas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Cuartel"
        verbose_name_plural = "Cuarteles"

    def __str__(self):
        return self.nombre


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
        return self.user.get_full_name() or self.user.username


class JCuadrilla(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Jefe de Cuadrilla"
        verbose_name_plural = "Jefes de Cuadrilla"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Cuadrilla(models.Model):
    nombre = models.CharField(max_length=100)
    jefe = models.ForeignKey(
        JCuadrilla, on_delete=models.PROTECT, related_name="cuadrillas"
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Cuadrilla"
        verbose_name_plural = "Cuadrillas"

    def __str__(self):
        return self.nombre


class Collera(models.Model):
    cuadrilla = models.ForeignKey(
        Cuadrilla, on_delete=models.CASCADE, related_name="colleras"
    )
    trabajador_1 = models.ForeignKey(
        Trabajador, on_delete=models.PROTECT, related_name="colleras_como_trabajador_1"
    )
    trabajador_2 = models.ForeignKey(
        Trabajador, on_delete=models.PROTECT, related_name="colleras_como_trabajador_2"
    )

    class Meta:
        ordering = ["cuadrilla__nombre", "id"]
        verbose_name = "Collera"
        verbose_name_plural = "Colleras"
        constraints = [
            models.CheckConstraint(
                check=~Q(trabajador_1=F("trabajador_2")),
                name="collera_trabajadores_distintos",
            ),
        ]

    def clean(self):
        super().clean()
        if self.trabajador_1_id and self.trabajador_1_id == self.trabajador_2_id:
            raise ValidationError(
                {"trabajador_2": "Una collera debe estar formada por dos trabajadores distintos."}
            )

    def __str__(self):
        return f"{self.trabajador_1} + {self.trabajador_2}"


class Labor(models.Model):
    class Estado(models.TextChoices):
        ACTIVA = "activa", "Activa"
        INACTIVA = "inactiva", "Inactiva"
        DETENIDA = "detenida", "Detenida"

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.ACTIVA,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Labor"
        verbose_name_plural = "Labores"

    def __str__(self):
        return self.nombre


class RegistroJornada(models.Model):
    class Calidad(models.TextChoices):
        EXPORTACION = "exportacion", "Exportación"
        NACIONAL = "nacional", "Nacional"
        INDUSTRIAL = "industrial", "Industrial"

    fecha = models.DateField(default=timezone.localdate)
    collera = models.ForeignKey(
        Collera, on_delete=models.PROTECT, related_name="jornadas"
    )
    cuartel = models.ForeignKey(
        Cuartel, on_delete=models.PROTECT, related_name="jornadas"
    )
    labor = models.ForeignKey(
        Labor, on_delete=models.PROTECT, related_name="jornadas"
    )
    asistencia_trabajador_1 = models.BooleanField(
        "Asistencia del trabajador 1", default=True
    )
    asistencia_trabajador_2 = models.BooleanField(
        "Asistencia del trabajador 2", default=True
    )
    kilos_producidos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    calidad = models.CharField(max_length=20, choices=Calidad.choices)
    kilos_perdida = models.DecimalField(
        "Kilos de pérdida",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    observaciones = models.TextField(blank=True)
    validado = models.BooleanField(default=False)
    validado_por = models.ForeignKey(
        JCuadrilla,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="jornadas_validadas",
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Registro de jornada"
        verbose_name_plural = "Registros de jornada"
        constraints = [
            models.CheckConstraint(
                check=Q(kilos_producidos__gte=0),
                name="jornada_kilos_producidos_no_negativos",
            ),
            models.CheckConstraint(
                check=Q(kilos_perdida__gte=0),
                name="jornada_kilos_perdida_no_negativos",
            ),
            models.CheckConstraint(
                check=(
                    Q(
                        validado=False,
                        validado_por__isnull=True,
                        fecha_validacion__isnull=True,
                    )
                    | Q(
                        validado=True,
                        validado_por__isnull=False,
                        fecha_validacion__isnull=False,
                    )
                ),
                name="jornada_validacion_consistente",
            ),
        ]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} · {self.collera} · {self.labor}"
