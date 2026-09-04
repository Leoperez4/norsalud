from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views, views_docente, views_estudiante

app_name = "panel"

urlpatterns = [
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("logout/", views.PanelLogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),

    # Recuperar contraseña (RF-02)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="panel/password_reset_form.html",
            email_template_name="panel/password_reset_email.html",
            subject_template_name="panel/password_reset_subject.txt",
            success_url=reverse_lazy("panel:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="panel/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirmar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="panel/password_reset_confirm.html",
            success_url=reverse_lazy("panel:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/completado/",
        auth_views.PasswordResetCompleteView.as_view(template_name="panel/password_reset_complete.html"),
        name="password_reset_complete",
    ),

    # Asignaturas
    path("asignaturas/", views.AsignaturaListView.as_view(), name="asignatura_list"),
    path("asignaturas/crear/", views.AsignaturaCreateView.as_view(), name="asignatura_create"),
    path("asignaturas/<int:pk>/", views.AsignaturaDetailView.as_view(), name="asignatura_detail"),
    path("asignaturas/<int:pk>/editar/", views.AsignaturaUpdateView.as_view(), name="asignatura_update"),
    path("asignaturas/<int:pk>/eliminar/", views.AsignaturaDeleteView.as_view(), name="asignatura_delete"),
    path("asignaturas/<int:pk>/estudiantes/", views.asignatura_estudiantes, name="asignatura_estudiantes"),
    path("inscripciones/<int:pk>/eliminar/", views.inscripcion_eliminar, name="inscripcion_eliminar"),

    # Programas
    path("programas/", views.programa_list, name="programa_list"),
    path("programas/<int:pk>/eliminar/", views.programa_eliminar, name="programa_eliminar"),

    # Docentes
    path("docentes/", views.DocenteListView.as_view(), name="docente_list"),
    path("docentes/agregar/", views.DocenteCreateView.as_view(), name="docente_create"),
    path("docentes/<int:pk>/", views.DocenteDetailView.as_view(), name="docente_detail"),
    path("docentes/<int:pk>/editar/", views.DocenteUpdateView.as_view(), name="docente_update"),
    path("docentes/<int:pk>/eliminar/", views.DocenteDeleteView.as_view(), name="docente_delete"),

    # Estudiantes
    path("estudiantes/", views.EstudianteListView.as_view(), name="estudiante_list"),
    path("estudiantes/agregar/", views.EstudianteCreateView.as_view(), name="estudiante_create"),
    path("estudiantes/<int:pk>/", views.EstudianteDetailView.as_view(), name="estudiante_detail"),
    path("estudiantes/<int:pk>/editar/", views.EstudianteUpdateView.as_view(), name="estudiante_update"),
    path("estudiantes/<int:pk>/eliminar/", views.EstudianteDeleteView.as_view(), name="estudiante_delete"),
    path("estudiantes/<int:pk>/notas/", views.estudiante_notas, name="estudiante_notas"),

    # Horario
    path("horario/", views.horario_list, name="horario"),
    path("horario/agregar/", views.HorarioCreateView.as_view(), name="horario_create"),
    path("horario/<int:pk>/eliminar/", views.HorarioDeleteView.as_view(), name="horario_delete"),

    # ---- Panel Docente ----
    path("docente/asignaturas/", views_docente.docente_asignaturas, name="docente_asignaturas"),
    path("docente/asignaturas/<int:pk>/asistencia/", views_docente.docente_asistencia, name="docente_asistencia"),
    path("docente/asignaturas/<int:pk>/tareas/", views_docente.docente_tareas, name="docente_tareas"),
    path("docente/asignaturas/<int:asignatura_pk>/tareas/crear/", views_docente.TareaCreateView.as_view(), name="docente_tarea_create"),
    path("docente/tareas/<int:pk>/editar/", views_docente.TareaUpdateView.as_view(), name="docente_tarea_update"),
    path("docente/tareas/<int:pk>/eliminar/", views_docente.TareaDeleteView.as_view(), name="docente_tarea_delete"),
    path("docente/tareas/<int:pk>/entregas/", views_docente.docente_tarea_entregas, name="docente_tarea_entregas"),
    path("docente/entregas/<int:pk>/calificar/", views_docente.EntregaCalificarView.as_view(), name="docente_entrega_calificar"),
    path("docente/asignaturas/<int:pk>/calificaciones/", views_docente.docente_calificaciones, name="docente_calificaciones"),
    path("docente/asignaturas/<int:pk>/calificaciones/pdf/", views_docente.docente_calificaciones_pdf, name="docente_calificaciones_pdf"),
    path("docente/asignaturas/<int:pk>/anuncios/", views_docente.docente_anuncios, name="docente_anuncios"),
    path("docente/horario/", views_docente.docente_horario, name="docente_horario"),

    # ---- Panel Estudiante ----
    path("estudiante/asignaturas/", views_estudiante.estudiante_asignaturas, name="estudiante_asignaturas"),
    path("estudiante/asignaturas/<int:pk>/tareas/", views_estudiante.estudiante_tareas, name="estudiante_tareas"),
    path("estudiante/tareas/<int:pk>/", views_estudiante.estudiante_tarea_detalle, name="estudiante_tarea_detalle"),
    path("estudiante/asignaturas/<int:pk>/anuncios/", views_estudiante.estudiante_anuncios, name="estudiante_anuncios"),
    path("estudiante/asignaturas/<int:pk>/calificaciones/", views_estudiante.estudiante_calificaciones, name="estudiante_calificaciones"),
    path("estudiante/asignaturas/<int:pk>/asistencias/", views_estudiante.estudiante_asistencias, name="estudiante_asistencias"),
    path("estudiante/horario/", views_estudiante.estudiante_horario, name="estudiante_horario"),
]
