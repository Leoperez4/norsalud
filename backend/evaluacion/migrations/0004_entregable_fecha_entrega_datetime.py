import datetime
from zoneinfo import ZoneInfo

from django.db import migrations, models


def cierre_a_fin_del_dia(apps, schema_editor):
    """Las tareas existentes solo tenían fecha: se cierran a las 11:59 p. m. (hora de Bogotá)."""
    Entregable = apps.get_model("evaluacion", "Entregable")
    bogota = ZoneInfo("America/Bogota")
    for tarea in Entregable.objects.all():
        # Tras AlterField el valor quedó como medianoche UTC de la fecha original.
        dia = tarea.fecha_entrega.date()
        tarea.fecha_entrega = datetime.datetime.combine(dia, datetime.time(23, 59), tzinfo=bogota)
        tarea.save(update_fields=["fecha_entrega"])


class Migration(migrations.Migration):

    dependencies = [
        ("evaluacion", "0003_entregaestudiante_comentario_estudiante"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entregable",
            name="fecha_entrega",
            field=models.DateTimeField(verbose_name="Fecha y hora límite de entrega"),
        ),
        migrations.RunPython(cierre_a_fin_del_dia, migrations.RunPython.noop),
    ]
