import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from academico.models import Asignatura, Horario, Inscripcion
from evaluacion.models import Anuncio, Asistencia, Entregable, EntregaEstudiante

from .forms_estudiante import SubirTareaForm


def _asignatura_del_estudiante(request, pk):
    """Devuelve la asignatura solo si el estudiante está inscrito en ella."""
    inscripcion = get_object_or_404(Inscripcion, asignatura_id=pk, estudiante=request.user)
    return inscripcion.asignatura


# ---------- Inicio estudiante ----------

@login_required
def estudiante_home(request):
    inscripciones = Inscripcion.objects.filter(estudiante=request.user).select_related("asignatura")
    asignatura_ids = [i.asignatura_id for i in inscripciones]

    entregadas_ids = EntregaEstudiante.objects.filter(
        estudiante=request.user, entregable__asignatura_id__in=asignatura_ids
    ).values_list("entregable_id", flat=True)

    tareas_pendientes = Entregable.objects.filter(
        asignatura_id__in=asignatura_ids
    ).exclude(pk__in=entregadas_ids).select_related("asignatura").order_by("fecha_entrega")[:6]

    notas_recientes = EntregaEstudiante.objects.filter(
        estudiante=request.user, calificacion__isnull=False
    ).select_related("entregable", "entregable__asignatura").order_by("-fecha_envio")[:5]

    anuncios_recientes = Anuncio.objects.filter(
        asignatura_id__in=asignatura_ids
    ).select_related("asignatura").order_by("-fecha_publicacion")[:5]

    hoy_dia = Horario.dia_de_hoy()
    clases_hoy = []
    if hoy_dia:
        clases_hoy = Horario.objects.filter(
            dia_semana=hoy_dia, asignatura_id__in=asignatura_ids
        ).select_related("asignatura").order_by("hora_inicio")

    return render(request, "panel/estudiante/dashboard.html", {
        "section": "inicio",
        "total_asignaturas": len(asignatura_ids),
        "tareas_pendientes": tareas_pendientes,
        "notas_recientes": notas_recientes,
        "anuncios_recientes": anuncios_recientes,
        "clases_hoy": clases_hoy,
        "hoy": datetime.date.today(),
    })


# ---------- Mis cursos (RF-39) ----------

@login_required
def estudiante_asignaturas(request):
    inscripciones = Inscripcion.objects.filter(estudiante=request.user).select_related(
        "asignatura", "asignatura__programa"
    )

    notas_por_asignatura = {}
    entregas_calificadas = EntregaEstudiante.objects.filter(
        estudiante=request.user, calificacion__isnull=False
    ).select_related("entregable")
    for entrega in entregas_calificadas:
        notas_por_asignatura.setdefault(entrega.entregable.asignatura_id, []).append(entrega.calificacion)

    for inscripcion in inscripciones:
        notas = notas_por_asignatura.get(inscripcion.asignatura_id)
        inscripcion.promedio = round(sum(notas) / len(notas), 2) if notas else None

    return render(request, "panel/estudiante/asignatura_list.html", {
        "section": "asignaturas",
        "inscripciones": inscripciones,
    })


# ---------- Tareas: subir y ver retroalimentación (RF-40 y RF-41) ----------

@login_required
def estudiante_tareas(request, pk):
    asignatura = _asignatura_del_estudiante(request, pk)
    hoy = datetime.date.today()
    entregas = {
        e.entregable_id: e for e in EntregaEstudiante.objects.filter(
            estudiante=request.user, entregable__asignatura=asignatura
        )
    }
    tareas = []
    for tarea in asignatura.entregables.order_by("numero"):
        entrega = entregas.get(tarea.pk)
        if entrega and entrega.calificacion is not None:
            estado = "calificada"
        elif entrega:
            estado = "entregada"
        elif tarea.fecha_entrega < hoy:
            estado = "vencida"
        else:
            estado = "pendiente"
        tareas.append({"tarea": tarea, "entrega": entrega, "estado": estado})

    return render(request, "panel/estudiante/tarea_list.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "tareas": tareas,
    })


@login_required
def estudiante_tarea_detalle(request, pk):
    tarea = get_object_or_404(Entregable, pk=pk)
    # Verifica que el estudiante esté inscrito en la asignatura de esta tarea.
    get_object_or_404(Inscripcion, asignatura=tarea.asignatura, estudiante=request.user)

    entrega = EntregaEstudiante.objects.filter(entregable=tarea, estudiante=request.user).first()
    ya_calificada = entrega and entrega.calificacion is not None

    if request.method == "POST" and not ya_calificada:
        form = SubirTareaForm(request.POST, request.FILES, instance=entrega)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.entregable = tarea
            entrega.estudiante = request.user
            entrega.save()
            messages.success(request, "Tarea enviada correctamente.")
            return redirect("panel:estudiante_tareas", pk=tarea.asignatura.pk)
    else:
        form = None if ya_calificada else SubirTareaForm(instance=entrega)

    return render(request, "panel/estudiante/tarea_detalle.html", {
        "section": "asignaturas",
        "tarea": tarea,
        "entrega": entrega,
        "form": form,
    })


# ---------- Anuncios (RF-42) ----------

@login_required
def estudiante_anuncios(request, pk):
    asignatura = _asignatura_del_estudiante(request, pk)
    anuncios = Anuncio.objects.filter(asignatura=asignatura)
    return render(request, "panel/estudiante/anuncios.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "anuncios": anuncios,
    })


# ---------- Planilla de calificaciones (RF-43) ----------

@login_required
def estudiante_calificaciones(request, pk):
    asignatura = _asignatura_del_estudiante(request, pk)
    entregas = EntregaEstudiante.objects.filter(
        estudiante=request.user, entregable__asignatura=asignatura
    ).select_related("entregable")
    notas = {e.entregable_id: e for e in entregas}

    filas = []
    valores = []
    for tarea in asignatura.entregables.order_by("numero"):
        entrega = notas.get(tarea.pk)
        if entrega and entrega.calificacion is not None:
            valores.append(entrega.calificacion)
        filas.append({"tarea": tarea, "entrega": entrega})

    promedio = round(sum(valores) / len(valores), 2) if valores else None

    return render(request, "panel/estudiante/calificaciones.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "filas": filas,
        "promedio": promedio,
    })


# ---------- Asistencias / fallas (RF-45) ----------

@login_required
def estudiante_asistencias(request, pk):
    asignatura = _asignatura_del_estudiante(request, pk)
    inscripcion = Inscripcion.objects.get(asignatura=asignatura, estudiante=request.user)
    fallas = Asistencia.objects.filter(inscripcion=inscripcion, estado=Asistencia.Estado.AUSENTE).order_by("-fecha")
    return render(request, "panel/estudiante/asistencias.html", {
        "section": "asignaturas",
        "asignatura": asignatura,
        "fallas": fallas,
    })


# ---------- Horario (RF-44) ----------

@login_required
def estudiante_horario(request):
    dia = request.GET.get("dia", Horario.Dia.LUNES)
    horarios = Horario.objects.filter(
        dia_semana=dia, asignatura__inscripciones__estudiante=request.user
    ).select_related("asignatura").distinct().order_by("hora_inicio")
    return render(request, "panel/estudiante/horario.html", {
        "section": "horario",
        "dias": Horario.Dia.choices,
        "dia_actual": dia,
        "horarios": horarios,
    })
