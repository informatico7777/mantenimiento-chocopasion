# Sistema de Gestión de Mantenimiento — Choco Pasión (Tingo María)

Aplicación web en **Django 5 + MySQL 8.4 (InnoDB)** para gestionar el mantenimiento
de la planta de producción de chocolate Choco Pasión: activos, checklist
preoperacional diario, observaciones, reportes de falla, órdenes de trabajo,
repuestos, energía, archivos técnicos descargables y reportes PDF.

La base de datos **`bd_mantenimiento_chocopasion` ya existe**. Todos los modelos se
mapean a las tablas reales con `managed = False` y `db_table`, por lo que Django
**no recrea ni altera** las tablas existentes.

---

## 1. Requisitos

- Python 3.10 o superior
- MySQL 8.4.x con la base `bd_mantenimiento_chocopasion` ya creada y poblada
  (ejecutar el script SQL del proyecto)
- pip / venv

## 2. Stack

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python |
| Framework | Django 5 |
| Base de datos | MySQL 8.4 / InnoDB |
| ORM | Django ORM (modelos `managed=False`) |
| Conector MySQL | `mysqlclient` (alternativa: `PyMySQL`) |
| Frontend | Django Templates + Bootstrap 5 + JS básico |
| PDF | WeasyPrint (respaldo automático con ReportLab) |
| Config | `python-decouple` + `.env` |

## 3. Instalación

```bash
# 1) Clonar / copiar el proyecto y entrar en la carpeta
cd mantenimiento_chocopasion

# 2) Crear y activar entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3) Instalar dependencias
pip install -r requirements.txt

# 4) Configurar variables de entorno
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/Mac
# Editar .env con las credenciales reales de MySQL
```

### Contenido de `.env`

```
SECRET_KEY=clave-secreta-de-desarrollo
DEBUG=True
DB_ENGINE=django.db.backends.mysql
DB_NAME=bd_mantenimiento_chocopasion
DB_USER=root
DB_PASSWORD=1234567AA
DB_HOST=localhost
DB_PORT=3306
ALLOWED_HOSTS=127.0.0.1,localhost
```

> La contraseña **nunca** se escribe en `settings.py`; se lee desde `.env`
> mediante `python-decouple`.

### Si `mysqlclient` falla al instalar en Windows

Use PyMySQL como alternativa:

```bash
pip install PyMySQL
```

Ya está habilitado en `config/__init__.py` (`pymysql.install_as_MySQLdb()`),
por lo que no requiere cambios adicionales.

## 4. Migraciones

La base ya existe y los modelos son `managed = False`, así que **`migrate` no
crea ni modifica las tablas de negocio**. Sin embargo, Django necesita sus propias
tablas internas (sesiones, auditoría de admin, etc.):

```bash
python manage.py migrate
```

Esto crea únicamente: `django_session`, `django_content_type`, `auth_permission`,
`django_admin_log`, `django_migrations`. Las 30 tablas del negocio permanecen
intactas.

> Las migraciones incluidas describen el estado de los modelos (necesario para el
> modelo de usuario personalizado) pero están marcadas `managed=False`: no tocan
> sus datos.

## 5. Definir la contraseña del usuario administrador

El registro `admin` insertado por el script SQL trae un hash de marcador de
posición. Asigne una contraseña real con el comando incluido:

```bash
python manage.py set_password admin --password "ClaveSegura123"
```

Esto guarda la contraseña con el hasher seguro PBKDF2 de Django en la columna
`password_hash`. Repita el comando para cualquier otro usuario.

## 6. Ejecutar

```bash
python manage.py runserver
```

Abra `http://127.0.0.1:8000/` → redirige a `/login/`.

## 7. Roles

| Rol | Capacidades principales |
|-----|--------------------------|
| `ADMINISTRADOR` | Acceso total |
| `JEFE_PRODUCCION` | Supervisión, libera máquinas, CRUD de catálogos y OT |
| `TECNICO_MANTENIMIENTO` | Ejecuta mantenimiento, OT, repuestos, servicios |
| `OPERADOR` | Checklist diario, observaciones, lotes |

El control por rol se aplica con el decorador `@rol_requerido(...)`
(`apps/accounts/decorators.py`). El `ADMINISTRADOR` siempre tiene acceso.

## 8. Páginas principales

```
/login/                              /ordenes/
/logout/                             /repuestos/
/dashboard/                          /proveedores/
/areas/                              /servicios-externos/
/maquinas/                           /produccion/lotes/
/maquinas/<id>/                      /energia/
/maquinas/crear/                     /documentos/
/maquinas/<id>/editar/               /reportes/
/checklist/plantillas/               /reportes/semanal/
/checklist/ejecutar/<id_maquina>/    /reportes/descargar/<id>/
/observaciones/
/fallas/
```

## 9. Reglas de negocio implementadas

1. Un checklist con un ítem `bloquea_produccion` no cumplido se marca **NO_APTA**
   y `permite_produccion = False`; la máquina pasa a **OBSERVADA** (con registro en
   `historial_estado_maquina`).
2. Desde un checklist no apto se puede **generar un reporte de falla**.
3. Una **observación crítica** se convierte en reporte de falla.
4. Un **reporte de falla** se convierte en **orden de trabajo** (correctiva).
5. La OT correctiva indica el tipo de atención (en planta, cambio de pieza,
   taller externo, máquina alternativa).
6. Todo **archivo subido** queda registrado en `archivos_adjuntos` y es
   descargable; se guarda en la subcarpeta de `media/` según su categoría.
7. Todo **reporte PDF** generado se guarda en `media/reportes_pdf/` y se registra
   en `reportes_generados` + `detalle_reportes_generados`.
8. Las acciones relevantes (login, logout, creación, edición, descarga,
   generación de reportes) se registran en `auditoria_sistema`.
9. El **dashboard** muestra alertas de repuestos bajo stock y mantenimientos
   vencidos.
10. El **reporte semanal PDF** consolida checklists, incumplimientos,
    observaciones, fallas, OT abiertas/cerradas, repuestos usados y bajo stock,
    consumo energético y recomendaciones de mantenimiento preventivo.

> El stock de repuestos lo actualiza automáticamente el **trigger** de MySQL al
> insertar en `movimiento_repuestos`; la aplicación solo registra el movimiento.

## 10. Estructura

```
mantenimiento_chocopasion/
├── manage.py
├── requirements.txt
├── .env.example
├── config/            # settings, urls, wsgi, asgi
├── apps/
│   ├── accounts/      # autenticación, roles, backend, decoradores
│   ├── core/          # áreas, máquinas, funciones, componentes, dashboard, auditoría
│   ├── mantenimiento/ # checklist, observaciones, fallas, planes, OT, mediciones
│   ├── inventario/    # repuestos, proveedores, movimientos, servicios externos
│   ├── produccion/    # lotes y consumo energético
│   ├── documentos/    # archivos adjuntos (subida/descarga)
│   └── reportes/      # reportes PDF, indicadores, auditoría
├── templates/         # base + módulos (Bootstrap 5)
├── static/            # css, js, img
└── media/             # maquinas, fichas_tecnicas, placas, manuales, evidencias, reportes_pdf
```

## 11. Notas sobre WeasyPrint

WeasyPrint requiere librerías del sistema (GTK/Pango/Cairo). Si no están
instaladas (típico en Windows), el generador de PDF **cae automáticamente** a
ReportLab y produce igualmente el reporte. Para PDF con el diseño HTML completo,
instale WeasyPrint siguiendo su documentación oficial para su sistema operativo.

## 12. Verificación

```bash
python manage.py check        # comprobación del sistema
python manage.py runserver
```

---

### Autenticación: detalle técnico

El modelo `accounts.Usuario` mapea la tabla `usuarios` e implementa la interfaz de
autenticación de Django sin heredar de `AbstractBaseUser` (la tabla no tiene
columna `last_login`). El backend `UsuarioLoginBackend` valida el `usuario_login`
y el `password_hash`. La señal `update_last_login` se desconecta en
`AccountsConfig.ready()`.
