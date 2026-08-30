from django.contrib import admin

from .models import Anuncio, Asistencia, Calificacion, Entregable, EntregaEstudiante


@admin.register(Entregable)
class EntregableAdmin(admin.ModelAdmin):
    list_display = ("id", "numero", "titulo", "asignatura", "fecha_entrega")
    list_filter = ("asignatura",)


@admin.register(EntregaEstudiante)
class EntregaEstudianteAdmin(admin.ModelAdmin):
    list_display = ("id", "entregable", "estudiante", "fecha_envio", "calificacion")
    list_filter = ("entregable",)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "inscripcion", "fecha", "estado")
    list_filter = ("estado", "fecha")


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ("id", "asignatura", "fecha_publicacion")
    list_filter = ("asignatura",)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("id", "inscripcion", "periodo", "promedio")
    list_filter = ("periodo",)
