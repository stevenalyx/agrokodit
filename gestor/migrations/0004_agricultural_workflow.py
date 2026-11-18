from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, Q
import django.utils.timezone


def crear_huertos_principales(apps, schema_editor):
    Predio = apps.get_model("gestor", "Predio")
    Huerto = apps.get_model("gestor", "Huerto")
    Cuartel = apps.get_model("gestor", "Cuartel")
    db_alias = schema_editor.connection.alias

    for predio in Predio.objects.using(db_alias).iterator():
        huerto = Huerto.objects.using(db_alias).create(
            predio_id=predio.pk,
            nombre="Huerto principal",
        )
        Cuartel.objects.using(db_alias).filter(predio_id=predio.pk).update(
            huerto_id=huerto.pk
        )


class Migration(migrations.Migration):

    dependencies = [
        ("gestor", "0003_auto_20261013_2248"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Huerto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=100)),
                (
                    "predio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="huertos",
                        to="gestor.predio",
                    ),
                ),
            ],
            options={
                "verbose_name": "Huerto",
                "verbose_name_plural": "Huertos",
                "ordering": ["predio__nombre", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="Administrador",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.group",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Administrador",
                "verbose_name_plural": "Administradores",
            },
        ),
        migrations.CreateModel(
            name="JCuadrilla",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.group",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Jefe de Cuadrilla",
                "verbose_name_plural": "Jefes de Cuadrilla",
            },
        ),
        migrations.CreateModel(
            name="Trabajador",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auth.group",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Trabajador",
                "verbose_name_plural": "Trabajadores",
            },
        ),
        migrations.CreateModel(
            name="Cuadrilla",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=100)),
                (
                    "jefe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cuadrillas",
                        to="gestor.jcuadrilla",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cuadrilla",
                "verbose_name_plural": "Cuadrillas",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Labor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=100, unique=True)),
                ("descripcion", models.TextField(blank=True)),
                ("activa", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Labor",
                "verbose_name_plural": "Labores",
                "ordering": ["nombre"],
            },
        ),
        migrations.AddField(
            model_name="cuartel",
            name="superficie_hectareas",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=8,
                null=True,
                validators=[MinValueValidator(Decimal("0.01"))],
            ),
        ),
        migrations.AddField(
            model_name="cuartel",
            name="huerto",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cuarteles",
                to="gestor.huerto",
            ),
        ),
        migrations.RunPython(
            crear_huertos_principales,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="cuartel",
            name="predio",
        ),
        migrations.AlterField(
            model_name="cuartel",
            name="huerto",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cuarteles",
                to="gestor.huerto",
            ),
        ),
        migrations.CreateModel(
            name="Collera",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "cuadrilla",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="colleras",
                        to="gestor.cuadrilla",
                    ),
                ),
                (
                    "trabajador_1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colleras_como_trabajador_1",
                        to="gestor.trabajador",
                    ),
                ),
                (
                    "trabajador_2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colleras_como_trabajador_2",
                        to="gestor.trabajador",
                    ),
                ),
            ],
            options={
                "verbose_name": "Collera",
                "verbose_name_plural": "Colleras",
                "ordering": ["cuadrilla__nombre", "id"],
            },
        ),
        migrations.CreateModel(
            name="RegistroJornada",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha", models.DateField(default=django.utils.timezone.localdate)),
                (
                    "asistencia_trabajador_1",
                    models.BooleanField(
                        default=True, verbose_name="Asistencia del trabajador 1"
                    ),
                ),
                (
                    "asistencia_trabajador_2",
                    models.BooleanField(
                        default=True, verbose_name="Asistencia del trabajador 2"
                    ),
                ),
                (
                    "kilos_producidos",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[MinValueValidator(Decimal("0"))],
                    ),
                ),
                (
                    "calidad",
                    models.CharField(
                        choices=[
                            ("exportacion", "Exportación"),
                            ("nacional", "Nacional"),
                            ("industrial", "Industrial"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "kilos_perdida",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0"),
                        max_digits=10,
                        validators=[MinValueValidator(Decimal("0"))],
                        verbose_name="Kilos de pérdida",
                    ),
                ),
                ("observaciones", models.TextField(blank=True)),
                ("validado", models.BooleanField(default=False)),
                ("fecha_validacion", models.DateTimeField(blank=True, null=True)),
                (
                    "collera",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="jornadas",
                        to="gestor.collera",
                    ),
                ),
                (
                    "cuartel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="jornadas",
                        to="gestor.cuartel",
                    ),
                ),
                (
                    "labor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="jornadas",
                        to="gestor.labor",
                    ),
                ),
                (
                    "validado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="jornadas_validadas",
                        to="gestor.jcuadrilla",
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de jornada",
                "verbose_name_plural": "Registros de jornada",
                "ordering": ["-fecha", "-id"],
            },
        ),
        migrations.DeleteModel(
            name="LecturaSensor",
        ),
        migrations.AddConstraint(
            model_name="collera",
            constraint=models.CheckConstraint(
                check=~Q(("trabajador_1", F("trabajador_2"))),
                name="collera_trabajadores_distintos",
            ),
        ),
        migrations.AddConstraint(
            model_name="registrojornada",
            constraint=models.CheckConstraint(
                check=Q(("kilos_producidos__gte", 0)),
                name="jornada_kilos_producidos_no_negativos",
            ),
        ),
        migrations.AddConstraint(
            model_name="registrojornada",
            constraint=models.CheckConstraint(
                check=Q(("kilos_perdida__gte", 0)),
                name="jornada_kilos_perdida_no_negativos",
            ),
        ),
        migrations.AddConstraint(
            model_name="registrojornada",
            constraint=models.CheckConstraint(
                check=(
                    Q(
                        ("fecha_validacion__isnull", True),
                        ("validado", False),
                        ("validado_por__isnull", True),
                    )
                    | Q(
                        ("fecha_validacion__isnull", False),
                        ("validado", True),
                        ("validado_por__isnull", False),
                    )
                ),
                name="jornada_validacion_consistente",
            ),
        ),
    ]
