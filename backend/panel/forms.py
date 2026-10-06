from django import forms

from academico.models import Asignatura, Horario, Programa
from accounts.models import Rol, Usuario

from .widgets import SelectorHora


class ConfirmarPasswordMixin:
    """Agrega el campo 'Confirmar contraseña' y valida que coincida con la contraseña."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned


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


class DocenteCreateForm(ConfirmarPasswordMixin, forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

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


class EstudianteCreateForm(ConfirmarPasswordMixin, forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

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
            "hora_inicio": SelectorHora(desde=6, hasta=21, attrs={"data-hora": "inicio"}),
            "hora_fin": SelectorHora(desde=6, hasta=22, attrs={"data-hora": "fin"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["hora_inicio"].widget.agregar_opcion_si_falta(self.instance.hora_inicio)
            self.fields["hora_fin"].widget.agregar_opcion_si_falta(self.instance.hora_fin)

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
