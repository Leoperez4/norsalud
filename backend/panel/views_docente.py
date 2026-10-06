import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from academico.models import Asignatura, Horario, Inscripcion
from evaluacion.models import Anuncio, Asistencia, Entregable, EntregaEstudiante

from .forms_docente import AnuncioForm, CalificarEntregaForm, EntregableForm
from .mixins import DocenteRequiredMixin


def _asignatura_del_docente(request, pk):
    """Devuelve la asignatura solo si pertenece al docente autenticado."""
    return get_object_or_404(Asignatura, pk=pk, docente=request.user)


# ---------- Inicio docente (RF-29) ----------

@login_required
def docente_home(request):
    asignaturas = Asignatura.objects.filter(docente=request.user).select_related("programa")

    entregas_por_calificar_qs = EntregaEstudiante.objects.filter(
        entregable__asignatura__docente=request.user, calificacion__isnull=True
    ).select_related("entregable", "entregable__asignatura", "estudiante").order_by("fecha_envio")

    hoy_dia = Horario.dia_de_hoy()
    clases_hoy = []
    if hoy_dia:
        clases_hoy = Horario.objects.filter(
            asignatura__docente=request.user, dia_semana=hoy_dia
        ).select_related("asignatura").order_by("hora_inicio")

    anuncios_recientes = Anuncio.objects.filter(
        asignatura__docente=request.user
    ).select_related("asignatura").order_by("-fecha_publicacion")[:5]

    total_por_calificar = entregas_por_calificar_qs.count()
    entregas_mostradas = list(entregas_por_calificar_qs[:6])

    return render(request, "panel/docente/dashboard.html", {
        "section": "inicio",
        "total_asignaturas": asignaturas.count(),
        "total_por_calificar": total_por_calificar,
        "entregas_por_calificar": entregas_mostradas,
        "entregas_restantes": total_por_calificar - len(entregas_mostradas),
        "clases_hoy": clases_hoy,
        "anuncios_recientes": anuncios_recientes,
    })


@login_required
def docente_asignaturas(request):
    asignaturas = Asignatura.objects.filter(docente=request.user).select_related("programa")
    return render(request, "panel/docente/asignatura_list.html", {
        "section": "asignaturas",
        "asignaturas": asignaturas,
    })


# ---------- Asistencia (RF-30) ----------

_DIAS = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]  # indexado por date.weekday()


def _ultimo_dia_de_clase(dias_clase, hoy):
    """Hoy si hay clase; si no, el día de clase más reciente (None si no hay horario)."""
    for atras in range(7):
        dia = hoy - datetime.timedelta(days=atras)
        if _DIAS[dia.weekday()] in dias_clase:
            return dia
    return None

@login_required
def docente_asistencia(request, pk):
    asignatura = _asignatura_del_docente(request, pk)
    hoy = datetime.date.today()
    dias_clase = set(asignatura.horarios.values_list("dia_semana", flat=True))

    fecha_str = request.GET.get("fecha") or request.POST.get("fecha")
    try:
        fecha = datetime.date.fromisoformat(fecha_str) if fecha_str else _ultimo_dia_de_clase(dias_clase, hoy)
    except ValueError:
        fecha = _ultimo_dia_de_clase(dias_clase, hoy)

    motivo_bloqueo = None
    if not dias_clase:
        motivo_bloqueo = "Esta asignatura no tiene horario asignado, así que no se puede llamar a lista."
    elif fecha is None or _DIAS[fecha.weekday()] not in dias_clase:
        dias_txt = ", ".join(
            etiqueta for codigo, etiqueta in Horario.Dia.choices if codigo in dias_clase
        )
        motivo_bloqueo = f"Esa fecha no es día de clase. Esta asignatura tiene clase los días: {dias_txt}."
    elif fecha > hoy:
        motivo_bloqueo = "No puedes llamar a lista en una fecha futura."

    inscripciones = Inscripcion.objects.filter(asignatura=asignatura).select_related("estudiante")

    if request.method == "POST":
        if motivo_bloqueo:
            messages.error(request, motivo_bloqueo)
            return redirect("panel:docente_asistencia", pk=asignatura.pk)
        for inscripcion in inscripciones:
            estado = request.POST.get(f"estado_{inscripcion.pk}")
            if estado in (Asistencia.Estado.PRESENTE, Asistencia.Estado.AUSENTE):
                Asistencia.objects.update_or_create(
                    inscripcion=inscripcion, fecha=fecha, defaults={"estado": estado}
                )
        messages.success(request, "Asistencia guardada correctamente.")
        return redirect("panel:docente_asignaturas")

    registros = {a.inscripcion_id: a.estado for a in Asistencia.objects.filter(
        inscripcion__asignatura=asignatura, fecha=fecha
    )}

    return render(request, "panel/docente/asistencia.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "fecha": fecha,
        "hoy": hoy,
        "dias_clase": sorted(_DIAS.index(d) for d in dias_clase),
        "motivo_bloqueo": motivo_bloqueo,
        "inscripciones": inscripciones,
        "registros": registros,
    })


# ---------- Tareas / entregables (RF-31 a RF-34) ----------

@login_required
def docente_tareas(request, pk):
    asignatura = _asignatura_del_docente(request, pk)
    tareas = []
    for tarea in asignatura.entregables.order_by("numero"):
        entregas = tarea.entregas.all()
        tareas.append({
            "tarea": tarea,
            "vencida": tarea.vencida,
            "entregadas": entregas.count(),
            "por_calificar": entregas.filter(calificacion__isnull=True).count(),
        })
    return render(request, "panel/docente/tarea_list.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "tareas": tareas,
    })


class TareaCreateView(DocenteRequiredMixin, CreateView):
    model = Entregable
    form_class = EntregableForm
    template_name = "panel/docente/tarea_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.asignatura = _asignatura_del_docente(request, kwargs["asignatura_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["asignatura"] = self.asignatura
        return kwargs

    def form_valid(self, form):
        form.instance.asignatura = self.asignatura
        messages.success(self.request, "Tarea creada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["asignatura"] = self.asignatura
        ctx["titulo"] = "Crear tarea"
        return ctx

    def get_success_url(self):
        return reverse("panel:docente_tareas", args=[self.asignatura.pk])


class TareaUpdateView(DocenteRequiredMixin, UpdateView):
    form_class = EntregableForm
    template_name = "panel/docente/tarea_form.html"

    def get_queryset(self):
        return Entregable.objects.filter(asignatura__docente=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Tarea actualizada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["asignatura"] = self.object.asignatura
        ctx["titulo"] = "Editar tarea"
        return ctx

    def get_success_url(self):
        return reverse("panel:docente_tareas", args=[self.object.asignatura.pk])


class TareaDeleteView(DocenteRequiredMixin, DeleteView):
    template_name = "panel/admin/confirmar_eliminar.html"

    def get_queryset(self):
        return Entregable.objects.filter(asignatura__docente=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["titulo"] = "Eliminar tarea"
        ctx["mensaje"] = f'¿Seguro que deseas eliminar la tarea "{self.object.titulo}"?'
        ctx["cancel_url"] = reverse("panel:docente_tareas", args=[self.object.asignatura.pk])
        return ctx

    def form_valid(self, form):
        asignatura_pk = self.object.asignatura.pk
        messages.success(self.request, "Tarea eliminada correctamente.")
        self.object.delete()
        return redirect("panel:docente_tareas", pk=asignatura_pk)

    def get_success_url(self):
        return reverse("panel:docente_tareas", args=[self.object.asignatura.pk])


@login_required
def docente_tarea_entregas(request, pk):
    """Ver entregas de una tarea, punto de partida para calificar (RF-34)."""
    tarea = get_object_or_404(Entregable, pk=pk, asignatura__docente=request.user)
    entregas = tarea.entregas.select_related("estudiante")
    return render(request, "panel/docente/tarea_entregas.html", {
        "section": "asignaturas",
        "tarea": tarea,
        "entregas": entregas,
    })


class EntregaCalificarView(DocenteRequiredMixin, UpdateView):
    """Asignar nota y retroalimentación a una entrega (RF-34 y RF-36)."""

    form_class = CalificarEntregaForm
    template_name = "panel/docente/calificar_entrega.html"

    def get_queryset(self):
        return EntregaEstudiante.objects.filter(entregable__asignatura__docente=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Calificación guardada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["section"] = "asignaturas"
        ctx["entrega"] = self.object
        return ctx

    def get_success_url(self):
        return reverse("panel:docente_tarea_entregas", args=[self.object.entregable.pk])


# ---------- Planilla de calificaciones (RF-35 y RF-36) ----------

@login_required
def docente_calificaciones(request, pk):
    asignatura = _asignatura_del_docente(request, pk)
    tareas = list(asignatura.entregables.order_by("numero"))
    inscripciones = Inscripcion.objects.filter(asignatura=asignatura).select_related("estudiante")

    entregas_por_estudiante = {}
    for entrega in EntregaEstudiante.objects.filter(entregable__asignatura=asignatura):
        entregas_por_estudiante.setdefault(entrega.estudiante_id, {})[entrega.entregable_id] = entrega

    filas = []
    for inscripcion in inscripciones:
        notas = entregas_por_estudiante.get(inscripcion.estudiante_id, {})
        valores = [notas[t.pk].calificacion for t in tareas if t.pk in notas and notas[t.pk].calificacion is not None]
        promedio = round(sum(valores) / len(valores), 2) if valores else None
        filas.append({
            "estudiante": inscripcion.estudiante,
            "notas": [notas.get(t.pk) for t in tareas],
            "promedio": promedio,
        })

    return render(request, "panel/docente/calificaciones.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "tareas": tareas,
        "filas": filas,
    })


@login_required
def docente_calificaciones_pdf(request, pk):
    """Exporta la planilla de calificaciones en PDF. Las tareas sin entrega cuentan como 0."""
    asignatura = _asignatura_del_docente(request, pk)
    tareas = list(asignatura.entregables.order_by("numero"))
    inscripciones = Inscripcion.objects.filter(asignatura=asignatura).select_related("estudiante")

    entregas_por_estudiante = {}
    for entrega in EntregaEstudiante.objects.filter(entregable__asignatura=asignatura):
        entregas_por_estudiante.setdefault(entrega.estudiante_id, {})[entrega.entregable_id] = entrega

    filas = []
    for inscripcion in inscripciones:
        notas = entregas_por_estudiante.get(inscripcion.estudiante_id, {})
        valores = []
        celdas = []
        for tarea in tareas:
            entrega = notas.get(tarea.pk)
            nota = entrega.calificacion if entrega and entrega.calificacion is not None else 0
            valores.append(nota)
            celdas.append(nota)
        promedio = round(sum(valores) / len(valores), 2) if valores else 0
        estudiante = inscripcion.estudiante
        filas.append([f"{estudiante.first_name} {estudiante.last_name}".strip() or estudiante.cedula, *celdas, promedio])

    return _generar_pdf_calificaciones(asignatura, tareas, filas)


def _generar_pdf_calificaciones(asignatura, tareas, filas):
    from io import BytesIO

    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Planilla de calificaciones — {asignatura.nombre} ({asignatura.curso})", styles["Title"]),
        Paragraph(f"Programa: {asignatura.programa} · Semestre: {asignatura.semestre}", styles["Normal"]),
        Spacer(1, 0.6 * cm),
    ]

    encabezado = ["Estudiante"] + [f"{t.numero}. {t.titulo}" for t in tareas] + ["Promedio"]
    data = [encabezado] + filas

    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e2a5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7ceea")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fc")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Nota: las tareas sin entrega registrada se contabilizan como 0 en esta planilla.",
        styles["Italic"],
    ))

    doc.build(story)
    buffer.seek(0)
    filename = f"calificaciones_{asignatura.nombre}_{asignatura.curso}.pdf".replace(" ", "_")
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ---------- Anuncios (RF-37) ----------

@login_required
def docente_anuncios(request, pk):
    asignatura = _asignatura_del_docente(request, pk)

    if request.method == "POST":
        form = AnuncioForm(request.POST)
        if form.is_valid():
            anuncio = form.save(commit=False)
            anuncio.asignatura = asignatura
            anuncio.save()
            messages.success(request, "Anuncio publicado correctamente.")
            return redirect("panel:docente_anuncios", pk=pk)
    else:
        form = AnuncioForm()

    anuncios = Anuncio.objects.filter(asignatura=asignatura)
    return render(request, "panel/docente/anuncios.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "anuncios": anuncios,
        "form": form,
    })


# ---------- Horario docente (RF-38) ----------

@login_required
def docente_horario(request):
    dia = request.GET.get("dia", Horario.Dia.LUNES)
    horarios = Horario.objects.filter(
        dia_semana=dia, asignatura__docente=request.user
    ).select_related("asignatura").order_by("hora_inicio")
    return render(request, "panel/docente/horario.html", {
        "section": "horario",
        "dias": Horario.Dia.choices,
        "dia_actual": dia,
        "horarios": horarios,
    })
