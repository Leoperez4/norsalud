# Norsalud — Plataforma académica

Plataforma web para la sistematización de procesos académicos del Instituto de formación en apoyo médico Norsalud S.A.S. (Tunja, Boyacá). Construida con Django y MariaDB.

## Requisitos previos

- **Python 3.11** — https://www.python.org/downloads/
- **MariaDB o MySQL**. La forma más fácil en Windows es instalar **XAMPP** (ya trae MariaDB y phpMyAdmin listos): https://www.apachefriends.org/
- **Git**

## Primera vez que instalas el proyecto

1. Clona el repositorio y entra a la carpeta:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd norsalud
   ```

2. Enciende MariaDB (desde el Panel de Control de XAMPP, botón "Start" en MySQL, o `C:\xampp\mysql_start.bat`).

3. Crea la base de datos y el usuario (una sola vez):
   ```bash
   C:\xampp\mysql\bin\mysql.exe -u root < setup_db.sql
   ```
   (o pega el contenido de `setup_db.sql` en la pestaña "SQL" de phpMyAdmin: http://localhost/phpmyadmin/)

4. Copia el archivo de variables de entorno:
   ```bash
   copy .env.example .env
   ```
   Los valores por defecto ya coinciden con `setup_db.sql`, no hace falta cambiar nada para desarrollo local.

5. Crea el entorno virtual de Python e instala las dependencias:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

6. Aplica las migraciones (crea todas las tablas):
   ```bash
   python manage.py migrate
   ```

7. Crea tu propio usuario administrador (cambia la cédula, correo y contraseña por los tuyos):
   ```bash
   python manage.py shell -c "
   from accounts.models import Usuario, Rol
   rol_admin = Rol.objects.get(nombre='Administrador')
   Usuario.objects.create_superuser(
       cedula='TU_CEDULA',
       email='tu_correo@ejemplo.com',
       password='TuContraseñaSegura123*',
       first_name='Tu nombre',
       last_name='Tu apellido',
       rol=rol_admin,
   )
   "
   ```

## Días siguientes (ya instalado)

Solo necesitas encender MariaDB y correr el servidor:
```bash
cd backend
venv\Scripts\activate
python manage.py runserver
```

## Acceder a la plataforma

| Herramienta | URL | Notas |
|---|---|---|
| Plataforma (login real) | http://localhost:8000/login/ | Usa la cédula/contraseña que creaste |
| Panel admin de Django | http://localhost:8000/admin/ | Mismas credenciales |
| phpMyAdmin (ver la BD) | http://localhost/phpmyadmin/ | Requiere que Apache de XAMPP también esté encendido |

## Si alguien más cambia los modelos (`models.py`)

Después de actualizar tu copia del código (`git pull`), aplica las migraciones nuevas:
```bash
python manage.py migrate
```

## Sobre `docker-compose.yml` y `Dockerfile`

El proyecto también incluye una configuración de Docker (usada en una etapa anterior del desarrollo). No es necesaria para correr el proyecto de forma local — se mantiene pensando en el despliegue en AWS más adelante. Instrucciones de instalación nativa (arriba) son las recomendadas para desarrollo en tu propio computador.
