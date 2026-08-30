from django.db import migrations


def crear_roles(apps, schema_editor):
    Rol = apps.get_model("accounts", "Rol")
    for nombre in ("Administrador", "Docente", "Estudiante"):
        Rol.objects.get_or_create(nombre=nombre)


def eliminar_roles(apps, schema_editor):
    Rol = apps.get_model("accounts", "Rol")
    Rol.objects.filter(nombre__in=("Administrador", "Docente", "Estudiante")).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_roles, eliminar_roles),
    ]
