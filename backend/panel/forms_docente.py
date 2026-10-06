from django import forms

from evaluacion.models import Anuncio, Entregable, EntregaEstudiante

from .widgets import FechaHoraWidget


class EntregableForm(forms.ModelForm):
    fecha_entrega = forms.SplitDateTimeField(
        label="Fecha y hora de cierre",
        widget=FechaHoraWidget,
        error_messages={"invalid": "Indica la fecha y la hora de cierre.", "required": "Indica la fecha y la hora de cierre."},
    )

    class Meta:
        model = Entregable
        fields = ["numero", "titulo", "descripcion", "fecha_entrega", "archivo_adjunto"]
        labels = {
            "numero": "Número de tarea",
            "titulo": "Nombre",
            "descripcion": "Descripción",
            "archivo_adjunto": "Archivo (opcional)",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, asignatura=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar, la asignatura viene de la tarea; al crear, la pasa la vista.
        self.asignatura = asignatura or getattr(self.instance, "asignatura", None)

    def clean_numero(self):
        numero = self.cleaned_data["numero"]
        if self.asignatura is not None:
            repetidas = Entregable.objects.filter(asignatura=self.asignatura, numero=numero)
            if self.instance.pk:
                repetidas = repetidas.exclude(pk=self.instance.pk)
            if repetidas.exists():
                raise forms.ValidationError(
                    f"Ya existe la tarea número {numero} en esta asignatura. Usa otro número."
                )
        return numero


class CalificarEntregaForm(forms.ModelForm):
    class Meta:
        model = EntregaEstudiante
        fields = ["calificacion", "retroalimentacion"]
        labels = {"calificacion": "Nota", "retroalimentacion": "Comentario de retroalimentación"}
        widgets = {"retroalimentacion": forms.Textarea(attrs={"rows": 3})}


class AnuncioForm(forms.ModelForm):
    class Meta:
        model = Anuncio
        fields = ["contenido"]
        labels = {"contenido": "Anuncio"}
        widgets = {"contenido": forms.Textarea(attrs={"rows": 4, "placeholder": "Escribe el anuncio para tus estudiantes..."})}
