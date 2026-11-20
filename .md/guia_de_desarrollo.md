# Guía de Desarrollo y Ejecución

## Entorno de Desarrollo (GitHub Codespaces)

* El servidor de base de datos es **MariaDB**, instalado dentro del Codespace (`sudo apt install mariadb-server`).
* Al reabrir el Codespace hay que iniciar el servicio: `sudo service mariadb start`.
* Base de datos: `AgroPeso`, con un usuario dedicado configurado en el archivo `.env`.
* Entorno virtual: Activar con `source env/bin/activate`.
* Dependencias: Instaladas vía `pip install -r requirements.txt`.
* Los scripts se ejecutan siempre posicionados desde la carpeta `backend/`.

---

---

## Entorno local en Windows (Visual Studio Code)

Desde la raíz del proyecto, en PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

* **Base de datos**: verificar el servicio con `Get-Service | Where-Object { $_.Name -match "mysql|maria" }` y, si está detenido, iniciarlo con `net start MariaDB` (o `MySQL80`) desde una terminal de administrador.
* **Backend**: `cd backend` y `uvicorn main:app --reload`.
* **Frontend**: en otra terminal, `cd frontend` y `python -m http.server 5500`.
* **CORS**: si se abre el front con `127.0.0.1`, incluir ambos orígenes en el `.env`: `CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500`.

---

## Ejecución del Proyecto

### 1. Levantar el Backend (API)
Con el entorno virtual activo y MariaDB encendido, desde la carpeta `backend/`:
```bash
uvicorn main:app --reload
```
La documentación interactiva (Swagger) estará disponible en `http://127.0.0.1:8000/docs`.

### 2. Levantar el Frontend
Desde la carpeta `frontend/`:
```bash
python3 -m http.server 5500
```
Abrir `http://localhost:5500/html/login.html` (o usar Live Server de VS Code). El punto de entrada es el login; según el rol, redirige al panel correspondiente.

*Nota sobre CORS:* `CORS_ORIGINS` en el `.env` define qué orígenes pueden consultar la API (ej: `http://localhost:5500`). Si usas Codespaces, asegúrate de añadir la URL generada o configurar los puertos correctamente.

---

## Base de Datos

### Actualizar una base de datos existente
Si la tabla `tickets` ya existía antes de implementar los estados, debes actualizarla manualmente, ya que `create_all` no altera tablas existentes:

```sql
sudo mysql AgroPeso -e "
ALTER TABLE tickets
  MODIFY peso_bruto INT NULL,
  MODIFY peso_neto INT NULL,
  ADD COLUMN estado VARCHAR(10) NOT NULL DEFAULT 'abierto';
UPDATE tickets SET estado = 'cerrado' WHERE peso_bruto IS NOT NULL;"
```
Desde AGROPESO-022 el nombre del proveedor es único. En una base existente hay que agregar la restricción a mano (antes, verificar que no haya nombres repetidos):

```sql
sudo mysql AgroPeso -e "ALTER TABLE suppliers ADD CONSTRAINT uq_suppliers_name UNIQUE (name);"
```

Desde AGROPESO-029 cada ticket tiene el campo `facturado`. Hay que agregar la columna **en la base local y en la de Railway antes de publicar** (si la API nueva arranca sin la columna, todas las consultas de tickets fallan con `500`):

```sql
ALTER TABLE tickets ADD COLUMN facturado BOOLEAN NOT NULL DEFAULT FALSE;
```

Los tickets que ya existían quedan como *no facturados*.

*A futuro, se implementarán migraciones con Alembic para evitar el uso de `ALTER TABLE` manual.*

---

---

## Seguridad y Variables de Entorno Adicionales (`backend/.env`)

Para la firma de tokens JWT, el archivo `.env` requiere las siguientes variables (nunca deben subirse al repositorio):

```env
SECRET_KEY=<clave generada con: python -c "import secrets; print(secrets.token_hex(32))">
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Tests
Los tests están construidos con `pytest` y se ejecutan desde la carpeta `backend/`:
```bash
pytest
```
* `test_schemas.py`: Valida los esquemas de Pydantic.
* `test_server.py`: Valida las reglas de negocio en memoria.
* `test_endpoints.py`: Verifica con `TestClient` los 401 (sin token o token inválido) y los 403 (cliente intentando escribir), sin base de datos. Los tests de 409/400 de proveedores sí usan la base real (con rollback).
* `test_backup.py`: Genera el SQL con un repositorio falso (escapado, `NULL`, fechas, orden de tablas), el guardado diario en una carpeta temporal y el endpoint (200 con `Content-Disposition` para admin, 403 cliente, 401 sin token).
* `test_repository.py`: Prueba contra la base real. Requiere MariaDB encendido; usa fixtures para deshacer los cambios (no deja basura en la BD).

---

## Filtros y exportación a Excel (frontend)

Desde AGROPESO-025 los paneles de admin y cliente filtran y exportan **en el navegador**, sin endpoints nuevos. La lógica común está en `frontend/js/exportar.js`, que se carga entre `auth.js` y el script de cada pantalla:

```html
<script src="../js/auth.js"></script>
<script src="../js/exportar.js"></script>
<script src="../js/admin.js"></script>  <!-- o cliente.js -->
```

| Función | Para qué sirve |
|---|---|
| `coincideConFiltros(t, filtros, textosExtra)` | Aplica todos los filtros con `AND`; un filtro vacío (`""`) no filtra |
| `rangoInvalido(desde, hasta)` | `true` si *Desde* es posterior a *Hasta* |
| `generarCSV(tickets, nombreProveedor, nombreProducto)` | Arma el CSV con encabezado, filas y fila de `TOTALES` |
| `nombreDeArchivo(partes, desde, hasta, hoy)` | Ej: `AgroPeso_Berg_2026-11-01_a_2026-11-20.csv` |
| `descargarCSV(nombre, contenido)` | Descarga con `Blob` + enlace temporal |
| `actualizarSelectFiltro(select, textoTodos, porId)` | Llena un `<select>` de filtro conservando la opción elegida |

### Formato del CSV

* **UTF-8 con BOM** (`\uFEFF`) para que Excel muestre tildes y ñ.
* **Separador `;`** (el que usa Excel con configuración regional en español) y fin de línea `CRLF`.
* **Textos entre comillas** con las comillas internas duplicadas (`Chofer "Pepe"` → `"Chofer ""Pepe"""`).
* **Números sin separador de miles** (`17040`) para que Excel los tome como números; `-` si no hay valor.
* **Protección contra fórmulas**: si un texto empieza con `=`, `+`, `@` o `-` seguido de algo, se le antepone `'` para que Excel no lo ejecute.

### Cómo probarlo a mano

1. Forzar la recarga (`Ctrl + Shift + R`). Si un cambio en `exportar.js` no se ve, cerrar la pestaña y volver a abrirla: el navegador puede seguir usando la versión en caché.
2. Exportar y abrir el `.csv` con doble clic en Excel: las columnas deben quedar separadas y la fila `TOTALES` al final.
3. Si Excel muestra todo en una sola columna, la configuración regional usa `,` como separador de listas: abrirlo con *Datos → Desde texto/CSV* y elegir `;`.

---

## Copias de seguridad de la base de datos

Desde AGROPESO-027 hay dos respaldos, los dos con el mismo formato (`agropeso_backup_YYYY-MM-DD.sql`), generados por `BackupService` con SQLAlchemy (no hace falta `mysqldump` en el `PATH`).

| Respaldo | Dónde queda | Cuándo |
|---|---|---|
| **Automático en el servidor** | `backend/backups/` (o la carpeta de la variable `BACKUP_DIR`) | Al arrancar la API y después cada 1 hora se fija si existe el archivo del día; si falta, lo crea |
| **Descarga del panel admin** | Carpeta de descargas del navegador | Solo cuando el admin toca **Descargar Backup DB** |

* `backend/backups/` está en `.gitignore`: los backups **no se suben** al repositorio (tienen los hashes de las contraseñas).
* El panel **nunca descarga solo**: si lo hiciera, bajaría un backup en cada PC donde se abra el panel de admin.
* En Railway el disco del contenedor **se borra en cada deploy o reinicio**: el backup automático del servidor sirve para el entorno local; en producción el respaldo real es el que descarga el admin (o los backups propios del servicio de MySQL de Railway).

### Restaurar un backup

El archivo tiene solo los datos (`INSERT`), no la estructura. Sobre una base **vacía**:

```powershell
cd backend
python create_table.py
& "C:\Program Files\MariaDB 13.0\bin\mysql.exe" -u root -p AgroPeso -e "source ruta/al/agropeso_backup_2026-11-20.sql"
```

Si la base ya tiene datos, los `INSERT` fallan por `id` duplicado: hay que vaciar las tablas antes (o restaurar en una base nueva).
