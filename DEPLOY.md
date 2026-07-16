# Guía de Despliegue - Sistema de Mantenimiento Choco Pasión

## Configuración para acceder a MySQL local desde la nube

### 1. Instalar y configurar ngrok (Túnel TCP)

ngrok permite exponer tu base de datos MySQL local a internet de forma segura.

**Pasos:**

1. Descargar ngrok: https://ngrok.com/download
2. Registrarse en ngrok y obtener el authtoken
3. Instalar el authtoken:
   ```bash
   ngrok authtoken TU_TOKEN_AQUI
   ```

4. Exponer MySQL (puerto 3306) mediante túnel TCP:
   ```bash
   ngrok tcp 3306
   ```

5. Anotar el host y puerto que ngrok proporciona, ejemplo:
   ```
   Forwarding: tcp://0.tcp.sa.ngrok.io:12345 -> localhost:3306
   ```
   - HOST: `0.tcp.sa.ngrok.io`
   - PORT: `12345`

**IMPORTANTE:** ngrok gratuito cambia la URL cada vez que reinicias. Para mantenerla fija necesitas el plan de pago.

### 2. Configurar acceso remoto en MySQL

Permite que MySQL acepte conexiones desde cualquier IP:

```sql
-- Conectarse a MySQL como root
mysql -u root -p

-- Crear usuario para acceso remoto (o modificar el existente)
CREATE USER 'root'@'%' IDENTIFIED BY '1234567AA';
GRANT ALL PRIVILEGES ON bd_mantenimiento_chocopasion.* TO 'root'@'%';
FLUSH PRIVILEGES;
```

Verificar que MySQL escucha en todas las interfaces (archivo `my.ini` o `my.cnf`):
```ini
[mysqld]
bind-address = 0.0.0.0
```

Reiniciar MySQL después de hacer el cambio.

### 3. Desplegar en Railway

**Opción A: Mediante GitHub (Recomendado)**

1. Crear repositorio en GitHub:
   ```bash
   cd mantenimiento_chocopasion
   git init
   git add .
   git commit -m "Initial commit - Sistema de Mantenimiento"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/mantenimiento-chocopasion.git
   git push -u origin main
   ```

2. Ir a https://railway.app y crear cuenta
3. Click en "New Project" → "Deploy from GitHub repo"
4. Seleccionar tu repositorio
5. Railway detectará automáticamente Django

**Opción B: Mediante Railway CLI**

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### 4. Configurar variables de entorno en Railway

En el dashboard de Railway, ir a "Variables" y agregar:

```
SECRET_KEY=genera-una-clave-secreta-segura-aqui
DEBUG=False
ALLOWED_HOSTS=*
DB_ENGINE=django.db.backends.mysql
DB_NAME=bd_mantenimiento_chocopasion
DB_USER=root
DB_PASSWORD=1234567AA
DB_HOST=0.tcp.sa.ngrok.io
DB_PORT=12345
```

**IMPORTANTE:** Reemplazar `DB_HOST` y `DB_PORT` con los valores de ngrok.

### 5. Generar una SECRET_KEY segura

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Verificar despliegue

Railway generará una URL automáticamente, ejemplo:
```
https://mantenimiento-chocopasion-production.up.railway.app
```

## Alternativa: Desplegar en Render

1. Crear cuenta en https://render.com
2. New → Web Service
3. Conectar repositorio de GitHub
4. Configurar:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn config.wsgi:application`
5. Agregar las mismas variables de entorno

## Mantenimiento del túnel

**Problema:** ngrok gratuito requiere que el túnel esté activo constantemente.

**Soluciones:**
1. Mantener ngrok corriendo en segundo plano en tu PC
2. Usar alternativas como `localhost.run` o `serveo.net`
3. Contratar ngrok de pago para URL fija
4. Migrar la base de datos a la nube (PlanetScale, Railway MySQL, etc.)

## Comandos útiles

Ejecutar migraciones en producción:
```bash
railway run python manage.py migrate
```

Crear superusuario:
```bash
railway run python manage.py createsuperuser
```

Ver logs:
```bash
railway logs
```

## Notas de seguridad

1. Nunca subir el archivo `.env` a GitHub
2. Usar contraseñas seguras para MySQL en producción
3. Configurar `ALLOWED_HOSTS` correctamente en producción
4. Considerar usar un firewall para restringir acceso al puerto MySQL
5. Rotación regular de SECRET_KEY
