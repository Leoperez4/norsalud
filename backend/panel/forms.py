from django import forms

from academico.models import Asignatura, Horario, Programa
from accounts.models import Rol, Usuario


class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ["nombre"]
        labels = {"nombre": "Nombre del programa"}
        widgets = {"nombre": forms.TextInput(attrs={"placeholder": "Ej. Auxiliar de enfermería"})}


class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ["nombre", "curso", "semestre", "programa", "docente", "cupos"]
        labels = {
            "nombre": "Nombre",
            "curso": "Curso",
            "semestre": "Semestre",
            "programa": "Programa",
            "docente": "Docente",
            "cupos": "Cupos",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["docente"].queryset = Usuario.objects.filter(rol__nombre=Rol.DOCENTE)
        self.fields["docente"].required = False


class DocenteCreateForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "cedula", "email", "programa", "celular", "direccion"]
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "cedula": "C.C.",
            "email": "Correo electrónico",
            "programa": "Programa",
            "celular": "Celular",
            "direccion": "Dirección",
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Rol.objects.get(nombre=Rol.DOCENTE)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


class DocenteEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "cedula", "email", "programa", "celular", "direccion"]
        labels = DocenteCreateForm.Meta.labels


class EstudianteCreateForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "cedula", "email", "programa", "celular", "direccion"]
        labels = DocenteCreateForm.Meta.labels

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Rol.objects.get(nombre=Rol.ESTUDIANTE)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario


class EstudianteEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "cedula", "email", "programa", "celular", "direccion"]
        labels = DocenteCreateForm.Meta.labels


class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ["asignatura", "salon", "dia_semana", "hora_inicio", "hora_fin"]
        labels = {
            "asignatura": "Asignatura",
            "salon": "Salón",
            "dia_semana": "Día",
            "hora_inicio": "Hora de inicio",
            "hora_fin": "Hora de finalización",
        }
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()
        salon = cleaned.get("salon")
        dia = cleaned.get("dia_semana")
        inicio = cleaned.get("hora_inicio")
        fin = cleaned.get("hora_fin")

        if inicio and fin and inicio >= fin:
            raise forms.ValidationError("La hora de inicio debe ser anterior a la hora de finalización.")

        if salon and dia and inicio and fin:
            traslape = Horario.objects.filter(
                salon=salon, dia_semana=dia, hora_inicio__lt=fin, hora_fin__gt=inicio
            )
            if self.instance.pk:
                traslape = traslape.exclude(pk=self.instance.pk)
            if traslape.exists():
                raise forms.ValidationError("El salón ya está ocupado en ese horario.")
        return cleaned
