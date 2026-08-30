from django.conf import settings
from django.db import models

from academico.models import Asignatura, Inscripcion


class Entregable(models.Model):
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="entregables"
    )
    numero = models.PositiveIntegerField("Número de tarea")
    titulo = models.CharField("Título", max_length=150)
    descripcion = models.TextField("Descripción")
    archivo_adjunto = models.FileField(
        "Archivo adjunto", upload_to="entregables/", blank=True, null=True
    )
    fecha_publicacion = models.DateTimeField("Fecha de publicación", auto_now_add=True)
    fecha_entrega = models.DateField("Fecha límite de entrega")

    class Meta:
        verbose_name = "Entregable"
        verbose_name_plural = "Entregables"

    def __str__(self):
        return f"{self.numero}. {self.titulo} ({self.asignatura})"


class EntregaEstudiante(models.Model):
    entregable = models.ForeignKey(
        Entregable, on_delete=models.CASCADE, related_name="entregas"
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="entregas",
        limit_choices_to={"rol__nombre": "Estudiante"},
    )
    archivo = models.FileField("Archivo", upload_to="entregas/")
    comentario_estudiante = models.TextField("Comentario del estudiante", blank=True)
    fecha_envio = models.DateTimeField("Fecha de envío", auto_now_add=True)
    retroalimentacion = models.TextField("Retroalimentación", blank=True)
    calificacion = models.DecimalField(
        "Calificación", max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Entrega de estudiante"
        verbose_name_plural = "Entregas de estudiantes"
        unique_together = ("entregable", "estudiante")

    def __str__(self):
        return f"{self.estudiante} -> {self.entregable}"


class Asistencia(models.Model):
    class Estado(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        AUSENTE = "AUSENTE", "Ausente"

    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE, related_name="asistencias"
    )
    fecha = models.DateField("Fecha de la clase")
    estado = models.CharField("Estado", max_length=10, choices=Estado.choices)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ("inscripcion", "fecha")

    def __str__(self):
        return f"{self.inscripcion.estudiante} - {self.fecha} - {self.estado}"


class Anuncio(models.Model):
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="anuncios"
    )
    contenido = models.TextField("Contenido")
    fecha_publicacion = models.DateTimeField("Fecha de publicación", auto_now_add=True)

    class Meta:
        verbose_name = "Anuncio"
        verbose_name_plural = "Anuncios"
        ordering = ["-fecha_publicacion"]

    def __str__(self):
        return f"Anuncio en {self.asignatura} ({self.fecha_publicacion:%d/%m/%Y})"


class Calificacion(models.Model):
    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE, related_name="calificaciones"
    )
    periodo = models.CharField("Periodo académico", max_length=50)
    promedio = models.DecimalField("Promedio", max_digits=5, decimal_places=2)
    fecha_registro = models.DateTimeField("Fecha de registro", auto_now_add=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        unique_together = ("inscripcion", "periodo")

    def __str__(self):
        return f"{self.inscripcion.estudiante} - {self.periodo}: {self.promedio}"
