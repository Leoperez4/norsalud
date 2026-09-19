from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from academico.models import Asignatura, Horario, Inscripcion, Programa
from accounts.models import Rol, Usuario
from evaluacion.models import Calificacion, EntregaEstudiante

from .forms import (
    AsignaturaForm,
    DocenteCreateForm,
    DocenteEditForm,
    EstudianteCreateForm,
    EstudianteEditForm,
    HorarioForm,
    ProgramaForm,
)
from .mixins import AdminRequiredMixin, admin_required


# ---------- Autenticación ----------

class PanelLoginView(LoginView):
    template_name = "panel/login.html"
    redirect_authenticated_user = True


class PanelLogoutView(LogoutView):
    next_page = "panel:login"


@login_required
def home(request):
    rol = getattr(request.user.rol, "nombre", None)
    if rol == "Administrador":
        return _admin_home(request)
    if rol == "Docente":
        from .views_docente import docente_home
        return docente_home(request)
    if rol == "Estudiante":
        from .views_estudiante import estudiante_home
        return estudiante_home(request)
    return render(request, "panel/pendiente.html", {"rol": rol})


def _admin_home(request):
    stats = {
        "estudiantes": Usuario.objects.filter(rol__nombre="Estudiante").count(),
        "docentes": Usuario.objects.filter(rol__nombre="Docente").count(),
        "asignaturas": Asignatura.objects.count(),
        "programas": Programa.objects.count(),
    }
    asignaturas_recientes = Asignatura.objects.select_related(
        "programa", "docente"
    ).order_by("-id")[:6]
    return render(request, "panel/admin/dashboard.html", {
        "section": "inicio",
        "stats": stats,
        "asignaturas_recientes": asignaturas_recientes,
    })


# ---------- Asignaturas (RF-03 a RF-11) ----------

class AsignaturaListView(AdminRequiredMixin, ListView):
    model = Asignatura
    template_name = "panel/admin/asignatura_list.html"
    context_object_name = "asignaturas"

    def get_queryset(self):
        return Asignatura.objects.select_related("programa", "docente").order_by("nombre")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        return ctx


class AsignaturaCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Asignatura
    form_class = AsignaturaForm
    template_name = "panel/admin/asignatura_form.html"
    success_url = reverse_lazy("panel:asignatura_list")
    success_message = "Asignatura creada correctamente."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["titulo"] = "Crear asignatura"
        return ctx


class AsignaturaUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Asignatura
    form_class = AsignaturaForm
    template_name = "panel/admin/asignatura_form.html"
    success_url = reverse_lazy("panel:asignatura_list")
    success_message = "Asignatura actualizada correctamente."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["titulo"] = "Editar asignatura"
        return ctx


class AsignaturaDetailView(AdminRequiredMixin, DetailView):
    model = Asignatura
    template_name = "panel/admin/asignatura_detail.html"
    context_object_name = "asignatura"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        return ctx


class AsignaturaDeleteView(AdminRequiredMixin, DeleteView):
    model = Asignatura
    template_name = "panel/admin/confirmar_eliminar.html"
    success_url = reverse_lazy("panel:asignatura_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["titulo"] = "Eliminar asignatura"
        ctx["mensaje"] = f'¿Seguro que deseas eliminar la asignatura "{self.object}"?'
        ctx["cancel_url"] = reverse_lazy("panel:asignatura_list")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Asignatura eliminada correctamente.")
        return super().form_valid(form)


@admin_required
def asignatura_estudiantes(request, pk):
    """Listado de estudiantes de la asignatura (RF-06) y matrícula (RF-07)."""
    asignatura = get_object_or_404(Asignatura, pk=pk)

    if request.method == "POST":
        estudiante_id = request.POST.get("estudiante")
        estudiante = get_object_or_404(Usuario, pk=estudiante_id, rol__nombre=Rol.ESTUDIANTE)
        if asignatura.cupos_ocupados >= asignatura.cupos:
            messages.error(request, "No hay cupos disponibles en esta asignatura.")
        elif Inscripcion.objects.filter(asignatura=asignatura, estudiante=estudiante).exists():
            messages.warning(request, "El estudiante ya está inscrito en esta asignatura.")
        else:
            Inscripcion.objects.create(asignatura=asignatura, estudiante=estudiante)
            messages.success(request, "Estudiante agregado correctamente.")
        return redirect("panel:asignatura_estudiantes", pk=pk)

    inscritos_ids = asignatura.inscripciones.values_list("estudiante_id", flat=True)
    estudiantes_disponibles = Usuario.objects.filter(rol__nombre=Rol.ESTUDIANTE).exclude(id__in=inscritos_ids)

    return render(request, "panel/admin/asignatura_estudiantes.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "inscripciones": asignatura.inscripciones.select_related("estudiante").order_by("estudiante__first_name"),
        "estudiantes_disponibles": estudiantes_disponibles,
    })


@admin_required
def inscripcion_eliminar(request, pk):
    """Retirar un estudiante de una asignatura (RF-08)."""
    inscripcion = get_object_or_404(Inscripcion, pk=pk)
    asignatura_id = inscripcion.asignatura_id
    inscripcion.delete()
    messages.success(request, "Estudiante retirado de la asignatura.")
    return redirect("panel:asignatura_estudiantes", pk=asignatura_id)


# ---------- Docentes (RF-12 a RF-17) ----------

class DocenteListView(AdminRequiredMixin, ListView):
    template_name = "panel/admin/docente_list.html"
    context_object_name = "docentes"

    def get_queryset(self):
        qs = Usuario.objects.filter(rol__nombre=Rol.DOCENTE).select_related("programa").order_by("first_name")
        cedula = self.request.GET.get("cedula", "").strip()
        if cedula:
            qs = qs.filter(cedula__icontains=cedula)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "docentes"
        ctx["cedula_buscada"] = self.request.GET.get("cedula", "")
        return ctx


class DocenteCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = DocenteCreateForm
    template_name = "panel/admin/usuario_form.html"
    success_url = reverse_lazy("panel:docente_list")
    success_message = "Docente registrado correctamente."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "docentes"
        ctx["titulo"] = "Agregar docente"
        return ctx


class DocenteUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = DocenteEditForm
    template_name = "panel/admin/usuario_form.html"
    success_url = reverse_lazy("panel:docente_list")
    success_message = "Información del docente actualizada."

    def get_queryset(self):
        return Usuario.objects.filter(rol__nombre=Rol.DOCENTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "docentes"
        ctx["titulo"] = "Editar docente"
        return ctx


class DocenteDetailView(AdminRequiredMixin, DetailView):
    template_name = "panel/admin/usuario_detail.html"
    context_object_name = "persona"

    def get_queryset(self):
        return Usuario.objects.filter(rol__nombre=Rol.DOCENTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "docentes"
        ctx["volver_url"] = reverse_lazy("panel:docente_list")
        return ctx


class DocenteDeleteView(AdminRequiredMixin, DeleteView):
    template_name = "panel/admin/confirmar_eliminar.html"
    success_url = reverse_lazy("panel:docente_list")

    def get_queryset(self):
        return Usuario.objects.filter(rol__nombre=Rol.DOCENTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "docentes"
        ctx["titulo"] = "Eliminar docente"
        ctx["mensaje"] = f"¿Seguro que deseas eliminar a {self.object}?"
        ctx["cancel_url"] = reverse_lazy("panel:docente_list")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Docente eliminado correctamente.")
        return super().form_valid(form)


# ---------- Estudiantes (RF-18 a RF-23, RF-46) ----------

class EstudianteListView(AdminRequiredMixin, ListView):
    template_name = "panel/admin/estudiante_list.html"
    context_object_name = "estudiantes"

    def get_queryset(self):
        qs = Usuario.objects.filter(rol__nombre=Rol.ESTUDIANTE).select_related("programa").order_by("first_name")
        cedula = self.request.GET.get("cedula", "").strip()
        if cedula:
            qs = qs.filter(cedula__icontains=cedula)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "estudiantes"
        ctx["cedula_buscada"] = self.request.GET.get("cedula", "")
        return ctx


class EstudianteCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = EstudianteCreateForm
    template_name = "panel/admin/usuario_form.html"
    success_url = reverse_lazy("panel:estudiante_list")
    success_message = "Estudiante matriculado correctamente."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "estudiantes"
        ctx["titulo"] = "Matricular estudiante"
        return ctx


class EstudianteUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = EstudianteEditForm
    template_name = "panel/admin/usuario_form.html"
    success_url = reverse_lazy("panel:estudiante_list")
    success_message = "Información del estudiante actualizada."

    def get_queryset(self):
        return Usuario.objects.filter(rol__nombre=Rol.ESTUDIANTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "estudiantes"
        ctx["titulo"] = "Editar estudiante"
        return ctx


class EstudianteDetailView(AdminRequiredMixin, DetailView):
    template_name = "panel/admin/usuario_detail.html"
    context_object_name = "persona"

    def get_queryset(self):
        return Usuario.objects.filter(rol__nombre=Rol.ESTUDIANTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "estudiantes"
        ctx["volver_url"] = reverse_lazy("panel:estudiante_list")
        return ctx


class EstudianteDeleteView(AdminRequiredMixin, DeleteView):
    template_name = "panel/admin/confirmar_eliminar.html"
    success_url = reverse_lazy("panel:estudiante_list")

    def get_queryset(self):
        return Usuario.objects.filter(rol__nombre=Rol.ESTUDIANTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "estudiantes"
        ctx["titulo"] = "Eliminar estudiante"
        ctx["mensaje"] = f"¿Seguro que deseas eliminar a {self.object}?"
        ctx["cancel_url"] = reverse_lazy("panel:estudiante_list")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Estudiante eliminado correctamente.")
        return super().form_valid(form)


@admin_required
def estudiante_matricular(request, pk):
    """Registrar/retirar al estudiante de asignaturas, desde su propia ficha."""
    estudiante = get_object_or_404(Usuario, pk=pk, rol__nombre=Rol.ESTUDIANTE)

    if request.method == "POST":
        asignatura = get_object_or_404(Asignatura, pk=request.POST.get("asignatura"))
        if asignatura.cupos_ocupados >= asignatura.cupos:
            messages.error(request, "No hay cupos disponibles en esa asignatura.")
        elif Inscripcion.objects.filter(asignatura=asignatura, estudiante=estudiante).exists():
            messages.warning(request, "El estudiante ya está registrado en esa asignatura.")
        else:
            Inscripcion.objects.create(asignatura=asignatura, estudiante=estudiante)
            messages.success(request, "Asignatura registrada correctamente.")
        return redirect("panel:estudiante_matricular", pk=pk)

    inscritas_ids = Inscripcion.objects.filter(estudiante=estudiante).values_list("asignatura_id", flat=True)
    asignaturas_disponibles = [
        a for a in Asignatura.objects.exclude(pk__in=inscritas_ids).select_related("programa")
        if a.cupos_disponibles > 0
    ]

    return render(request, "panel/admin/estudiante_matricular.html", {
        "section": "estudiantes",
        "estudiante": estudiante,
        "inscripciones": Inscripcion.objects.filter(estudiante=estudiante)
            .select_related("asignatura", "asignatura__programa").order_by("asignatura__nombre"),
        "asignaturas_disponibles": asignaturas_disponibles,
    })


@admin_required
def estudiante_inscripcion_retirar(request, pk, inscripcion_pk):
    inscripcion = get_object_or_404(Inscripcion, pk=inscripcion_pk, estudiante_id=pk)
    inscripcion.delete()
    messages.success(request, "Estudiante retirado de la asignatura.")
    return redirect("panel:estudiante_matricular", pk=pk)


@admin_required
def estudiante_notas(request, pk):
    """Promedio del estudiante en cada una de sus asignaturas (RF-46)."""
    estudiante = get_object_or_404(Usuario, pk=pk, rol__nombre=Rol.ESTUDIANTE)
    inscripciones = Inscripcion.objects.filter(estudiante=estudiante).select_related("asignatura")

    notas_por_asignatura = {}
    entregas = EntregaEstudiante.objects.filter(
        estudiante=estudiante, calificacion__isnull=False
    ).select_related("entregable")
    for entrega in entregas:
        notas_por_asignatura.setdefault(entrega.entregable.asignatura_id, []).append(entrega.calificacion)

    filas = []
    for inscripcion in inscripciones:
        notas = notas_por_asignatura.get(inscripcion.asignatura_id)
        promedio = round(sum(notas) / len(notas), 2) if notas else None
        filas.append({"asignatura": inscripcion.asignatura, "promedio": promedio})

    return render(request, "panel/admin/estudiante_notas.html", {
        "section": "estudiantes",
        "estudiante": estudiante,
        "filas": filas,
    })


# ---------- Horario (RF-24 a RF-28) ----------

@admin_required
def horario_list(request):
    dia = request.GET.get("dia", Horario.Dia.LUNES)
    horarios = Horario.objects.filter(dia_semana=dia).select_related("asignatura", "asignatura__docente").order_by(
        "hora_inicio"
    )
    return render(request, "panel/admin/horario_list.html", {
        "section": "horario",
        "dias": Horario.Dia.choices,
        "dia_actual": dia,
        "horarios": horarios,
    })


class HorarioCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = HorarioForm
    template_name = "panel/admin/horario_form.html"
    success_url = reverse_lazy("panel:horario")
    success_message = "Clase agregada correctamente al horario."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "horario"
        ctx["titulo"] = "Agregar clase"
        return ctx


class HorarioDeleteView(AdminRequiredMixin, DeleteView):
    model = Horario
    template_name = "panel/admin/confirmar_eliminar.html"
    success_url = reverse_lazy("panel:horario")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "horario"
        ctx["titulo"] = "Eliminar clase"
        ctx["mensaje"] = f"¿Seguro que deseas eliminar esta clase del horario?\n{self.object}"
        ctx["cancel_url"] = reverse_lazy("panel:horario")
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Clase eliminada del horario.")
        return super().form_valid(form)


# ---------- Programas ----------

@admin_required
def programa_list(request):
    """Listado de programas y alta rápida (los usan Asignaturas, Docentes y Estudiantes)."""
    if request.method == "POST":
        form = ProgramaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Programa creado correctamente.")
            return redirect("panel:programa_list")
    else:
        form = ProgramaForm()

    programas = Programa.objects.order_by("nombre")
    return render(request, "panel/admin/programa_list.html", {
        "section": "asignaturas",
        "programas": programas,
        "form": form,
    })


class ProgramaUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Programa
    form_class = ProgramaForm
    template_name = "panel/admin/programa_form.html"
    success_url = reverse_lazy("panel:programa_list")
    success_message = "Programa actualizado correctamente."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["titulo"] = "Editar programa"
        return ctx


@admin_required
def programa_eliminar(request, pk):
    programa = get_object_or_404(Programa, pk=pk)
    try:
        programa.delete()
        messages.success(request, "Programa eliminado correctamente.")
    except ProtectedError:
        messages.error(
            request,
            "No se puede eliminar: hay asignaturas registradas con este programa. "
            "Reasígnalas o elimínalas primero.",
        )
    return redirect("panel:programa_list")
