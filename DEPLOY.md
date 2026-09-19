# Despliegue en el VPS (producción)

Esta guía asume un VPS Ubuntu/Debian limpio, con un dominio ya comprado, y
que vas a correr todo (app + base de datos) con Docker.

## 0. Antes de empezar

- Apunta el DNS de tu dominio (registro **A**) a la IP pública del VPS.
  Espera a que propague (`ping tudominio.com` debe responder con la IP del VPS).
- Necesitas: acceso SSH al VPS, y el dominio ya apuntando.

## 1. Instalar Docker en el VPS

```bash
ssh usuario@IP_DEL_VPS

curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# cierra sesión y vuelve a entrar para que el grupo tome efecto
```

Verifica: `docker compose version` (Docker moderno ya trae Compose integrado).

## 2. Firewall básico

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

No abras el puerto 3306 (MariaDB) al exterior — en `docker-compose.prod.yml`
la base de datos solo es accesible dentro de la red interna de Docker.

## 3. Clonar el repositorio

```bash
git clone https://github.com/Leoperez4/norsalud.git
cd norsalud
```

## 4. Configurar `.env`

```bash
cp .env.example .env
nano .env
```

Ajusta como mínimo:

```
DEBUG=0
SECRET_KEY=<genera una clave larga y aleatoria, no la del ejemplo>
ALLOWED_HOSTS=tudominio.com
CSRF_TRUSTED_ORIGINS=https://tudominio.com

DB_NAME=norsalud
DB_USER=norsalud_user
DB_PASSWORD=<contraseña fuerte, distinta a la de desarrollo>
DB_ROOT_PASSWORD=<otra contraseña fuerte>
DB_HOST=db
DB_PORT=3306

DOMAIN=tudominio.com
CERTBOT_EMAIL=tu_correo@ejemplo.com

SECURE_SSL_REDIRECT=1
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
SECURE_HSTS_SECONDS=31536000
```

Para generar un `SECRET_KEY` seguro:
```bash
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 4.1 Activar el envío real de correos ("¿Olvidaste tu contraseña?")

⚠️ **Importante**: si dejas el `.env` como está, la función "¿Olvidaste tu
contraseña?" del login **no envía correos reales** — el enlace de
recuperación solo queda impreso en los logs del contenedor `web`
(`docker compose -f docker-compose.prod.yml logs web`), que ningún usuario
va a poder ver. Para que un estudiante o docente real reciba el correo,
hay que activar el envío por SMTP antes de poner la plataforma en manos de
usuarios.

Con una cuenta de Gmail:

1. Activa la verificación en dos pasos en esa cuenta de Gmail (requisito
   para el siguiente paso): https://myaccount.google.com/security
2. Genera una "contraseña de aplicación" (16 caracteres, distinta a la
   contraseña normal de la cuenta): https://myaccount.google.com/apppasswords
3. En el `.env` del VPS, descomenta y completa estas 3 líneas:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST_USER=tu_correo@gmail.com
   EMAIL_HOST_PASSWORD=<la contraseña de aplicación de 16 caracteres, sin espacios>
   ```
4. Reinicia el contenedor `web` para que tome el `.env` nuevo:
   ```bash
   docker compose -f docker-compose.prod.yml up -d web
   ```
5. Prueba el flujo real: entra a `https://tudominio.com/password-reset/`,
   pide la recuperación con un correo que puedas revisar, y confirma que
   llega el correo (revisa spam la primera vez).

Si no usan Gmail sino otro proveedor (Outlook, un correo institucional,
SendGrid, etc.), el mismo mecanismo aplica pero cambian `EMAIL_HOST`,
`EMAIL_PORT` y `EMAIL_USE_TLS` en `backend/config/settings.py` — Gmail está
hardcodeado ahí como valor por defecto porque es lo más común para un
proyecto de este tamaño.

## 5. Levantar la base de datos y la app (sin HTTPS todavía)

```bash
docker compose -f docker-compose.prod.yml up -d db web
docker compose -f docker-compose.prod.yml logs -f web
```

La primera vez, `web` corre migraciones y `collectstatic` automáticamente
(ver `backend/entrypoint.sh`). Espera a ver el log de Gunicorn arrancado.

## 6. Emitir el certificado HTTPS (Let's Encrypt)

Solo la primera vez:

```bash
chmod +x deploy/init-letsencrypt.sh
./deploy/init-letsencrypt.sh
```

Este script:
1. Crea un certificado autofirmado temporal para poder levantar nginx.
2. Levanta nginx.
3. Le pide a Let's Encrypt el certificado real para tu dominio.
4. Recarga nginx con el certificado definitivo.

El contenedor `certbot` queda corriendo en segundo plano renovando el
certificado automáticamente cada 12 horas (solo renueva si falta poco para
que expire, así que no hace daño que corra seguido).

## 7. Levantar todo

```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Abre `https://tudominio.com` — deberías ver el login de Norsalud con
candado verde.

## 8. Crear tu usuario administrador

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell -c "
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

## Actualizar la app después de un cambio en el código

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build web
```

El `entrypoint.sh` vuelve a correr migraciones y `collectstatic`
automáticamente al reiniciar el contenedor `web`.

## Backups de la base de datos

```bash
docker compose -f docker-compose.prod.yml exec db \
  sh -c 'exec mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" norsalud' > backup_$(date +%F).sql
```

Prográmalo con un cron en el VPS (fuera de Docker) apuntando a este comando.

## Notas

- `docker-compose.yml` (sin `.prod`) queda como estaba, pensado solo para
  pruebas locales rápidas con Docker si alguna vez lo necesitas — **no**
  es el que se usa en el VPS.
- Los archivos subidos por estudiantes/docentes (`media/`) y los archivos
  estáticos viven en volúmenes de Docker (`media_volume`, `static_volume`),
  no se pierden al reconstruir el contenedor `web`.
