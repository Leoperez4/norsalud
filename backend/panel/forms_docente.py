from django import forms

from evaluacion.models import Anuncio, Entregable, EntregaEstudiante


class EntregableForm(forms.ModelForm):
    class Meta:
        model = Entregable
        fields = ["numero", "titulo", "descripcion", "fecha_entrega", "archivo_adjunto"]
        labels = {
            "numero": "Número de tarea",
            "titulo": "Nombre",
            "descripcion": "Descripción",
            "fecha_entrega": "Fecha de cierre",
            "archivo_adjunto": "Archivo (opcional)",
        }
        widgets = {
            "fecha_entrega": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }


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
