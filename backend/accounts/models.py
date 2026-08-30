from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.Model):
    ADMINISTRADOR = "Administrador"
    DOCENTE = "Docente"
    ESTUDIANTE = "Estudiante"

    nombre = models.CharField("Nombre del rol", max_length=50, unique=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, cedula, email, password=None, **extra_fields):
        if not cedula:
            raise ValueError("La cédula es obligatoria")
        if not email:
            raise ValueError("El correo es obligatorio")
        email = self.normalize_email(email)
        usuario = self.model(cedula=cedula, email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, cedula, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(cedula, email, password, **extra_fields)


class Usuario(AbstractUser):
    username = None

    cedula = models.CharField("Cédula", max_length=20, unique=True)
    email = models.EmailField("Correo electrónico", unique=True)
    celular = models.CharField("Celular", max_length=20, blank=True)
    direccion = models.CharField("Dirección", max_length=255, blank=True)
    rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT, related_name="usuarios", verbose_name="Rol"
    )
    programa = models.ForeignKey(
        "academico.Programa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="Programa",
    )

    USERNAME_FIELD = "cedula"
    REQUIRED_FIELDS = ["email", "rol"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.cedula})"
