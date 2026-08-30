from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse


class AdminRequiredMixin(LoginRequiredMixin):
    login_url = "panel:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            rol = getattr(request.user.rol, "nombre", None)
            if rol != "Administrador":
                return redirect("panel:home")
        return super().dispatch(request, *args, **kwargs)


class DocenteRequiredMixin(LoginRequiredMixin):
    login_url = "panel:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            rol = getattr(request.user.rol, "nombre", None)
            if rol != "Docente":
                return redirect("panel:home")
        return super().dispatch(request, *args, **kwargs)


class EstudianteRequiredMixin(LoginRequiredMixin):
    login_url = "panel:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            rol = getattr(request.user.rol, "nombre", None)
            if rol != "Estudiante":
                return redirect("panel:home")
        return super().dispatch(request, *args, **kwargs)


def admin_required(view_func):
    """Equivalente a AdminRequiredMixin, pero para vistas basadas en función."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('panel:login')}?next={request.path}")
        rol = getattr(request.user.rol, "nombre", None)
        if rol != "Administrador":
            return redirect("panel:home")
        return view_func(request, *args, **kwargs)

    return wrapper
