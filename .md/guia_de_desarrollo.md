# Guía de Desarrollo y Ejecución

## Entorno de Desarrollo (GitHub Codespaces)

* El servidor de base de datos es **MariaDB**, instalado dentro del Codespace (`sudo apt install mariadb-server`).
* Al reabrir el Codespace hay que iniciar el servicio: `sudo service mariadb start`.
* Base de datos: `AgroPeso`, con un usuario dedicado configurado en el archivo `.env`.
* Entorno virtual: Activar con `source env/bin/activate`.
* Dependencias: Instaladas vía `pip install -r requirements.txt`.
* Los scripts se ejecutan siempre posicionados desde la carpeta `backend/`.

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
Abrir `http://localhost:5500/html/index.html` (o usar Live Server de VS Code).

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
*A futuro, se implementarán migraciones con Alembic para evitar el uso de `ALTER TABLE` manual.*

---

## Tests
Los tests están construidos con `pytest` y se ejecutan desde la carpeta `backend/`:
```bash
pytest
```
* `test_schemas.py`: Valida los esquemas de Pydantic.
* `test_server.py`: Valida las reglas de negocio en memoria.
* `test_repository.py`: Prueba contra la base real. Requiere MariaDB encendido; usa fixtures para deshacer los cambios (no deja basura en la BD).