from django.db import migrations, models


def migrar_estado_labor(apps, schema_editor):
    Labor = apps.get_model("gestor", "Labor")
    Labor.objects.filter(activa=True).update(estado="activa")
    Labor.objects.filter(activa=False).update(estado="inactiva")


def restaurar_estado_labor(apps, schema_editor):
    Labor = apps.get_model("gestor", "Labor")
    Labor.objects.filter(estado="activa").update(activa=True)
    Labor.objects.exclude(estado="activa").update(activa=False)


class Migration(migrations.Migration):
    dependencies = [("gestor", "0004_agricultural_workflow")]

    operations = [
        migrations.AddField(
            model_name="labor",
            name="estado",
            field=models.CharField(
                choices=[
                    ("activa", "Activa"),
                    ("inactiva", "Inactiva"),
                    ("detenida", "Detenida"),
                ],
                default="activa",
                max_length=10,
            ),
        ),
        migrations.RunPython(migrar_estado_labor, restaurar_estado_labor),
        migrations.RemoveField(model_name="labor", name="activa"),
    ]
