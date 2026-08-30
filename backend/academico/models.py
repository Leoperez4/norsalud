from django.conf import settings
from django.db import models


class Programa(models.Model):
    nombre = models.CharField("Nombre del programa", max_length=150)

    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"

    def __str__(self):
        return self.nombre


class Asignatura(models.Model):
    nombre = models.CharField("Nombre", max_length=150)
    curso = models.CharField("Curso", max_length=100)
    semestre = models.CharField("Semestre", max_length=20)
    programa = models.ForeignKey(
        Programa, on_delete=models.PROTECT, related_name="asignaturas"
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asignaturas_dictadas",
        limit_choices_to={"rol__nombre": "Docente"},
    )
    cupos = models.PositiveIntegerField("Cupos")

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"

    def __str__(self):
        return f"{self.nombre} - {self.curso}"

    @property
    def cupos_ocupados(self):
        return self.inscripciones.count()

    @property
    def cupos_disponibles(self):
        return self.cupos - self.cupos_ocupados


class Inscripcion(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscripciones",
        limit_choices_to={"rol__nombre": "Estudiante"},
    )
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="inscripciones"
    )
    fecha_registro = models.DateField("Fecha de inscripción", auto_now_add=True)

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        unique_together = ("estudiante", "asignatura")

    def __str__(self):
        return f"{self.estudiante} en {self.asignatura}"


class Horario(models.Model):
    class Dia(models.TextChoices):
        LUNES = "LUN", "Lunes"
        MARTES = "MAR", "Martes"
        MIERCOLES = "MIE", "Miércoles"
        JUEVES = "JUE", "Jueves"
        VIERNES = "VIE", "Viernes"

    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="horarios"
    )
    salon = models.CharField("Salón", max_length=50)
    dia_semana = models.CharField("Día", max_length=3, choices=Dia.choices)
    hora_inicio = models.TimeField("Hora de inicio")
    hora_fin = models.TimeField("Hora de finalización")

    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"

    def __str__(self):
        return f"{self.asignatura} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"
