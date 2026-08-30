from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Rol, Usuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ("cedula",)
    list_display = ("cedula", "first_name", "last_name", "email", "rol", "programa", "is_staff")
    search_fields = ("cedula", "first_name", "last_name", "email")
    fieldsets = (
        (None, {"fields": ("cedula", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email", "celular", "direccion")}),
        ("Rol y programa", {"fields": ("rol", "programa")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("cedula", "email", "password1", "password2", "rol", "programa"),
        }),
    )
