from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Asignatura, Horario, Inscripcion, Programa


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")


class InscripcionInline(admin.TabularInline):
    """Muestra el listado de estudiantes inscritos dentro de la asignatura (RF-06)."""

    model = Inscripcion
    fields = ("estudiante", "fecha_registro")
    readonly_fields = ("estudiante", "fecha_registro")
    extra = 0
    max_num = 0
    can_delete = False
    verbose_name_plural = "Estudiantes inscritos"


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nombre", "curso", "semestre", "programa", "docente",
        "cupos", "cupos_ocupados", "agregar_estudiante_link",
    )
    list_filter = ("programa", "semestre")
    readonly_fields = ("agregar_estudiante_link",)
    fields = (
        "nombre", "curso", "semestre", "programa", "docente", "cupos",
        "agregar_estudiante_link",
    )
    inlines = [InscripcionInline]

    def agregar_estudiante_link(self, obj):
        """Botón que redirige al formulario de Inscripciones (RF-07), con la asignatura preseleccionada."""
        if not obj.pk:
            return "Guarda la asignatura primero"
        url = reverse("admin:academico_inscripcion_add") + f"?asignatura={obj.pk}"
        return format_html('<a class="button" href="{}">+ Agregar estudiante</a>', url)

    agregar_estudiante_link.short_description = "Matricular estudiante"


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ("id", "estudiante", "asignatura", "fecha_registro")
    list_filter = ("asignatura",)


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("id", "asignatura", "salon", "dia_semana", "hora_inicio", "hora_fin")
    list_filter = ("dia_semana",)
