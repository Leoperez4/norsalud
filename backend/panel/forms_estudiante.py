from django import forms

from evaluacion.models import EntregaEstudiante


class SubirTareaForm(forms.ModelForm):
    class Meta:
        model = EntregaEstudiante
        fields = ["archivo", "comentario_estudiante"]
        labels = {
            "archivo": "Archivo de la tarea",
            "comentario_estudiante": "Comentario (opcional)",
        }
        widgets = {
            "comentario_estudiante": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Agrega una nota para tu docente sobre esta entrega...",
            }),
        }
