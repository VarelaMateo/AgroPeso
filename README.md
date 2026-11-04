# AgroPeso
Es una plataforma web para la gestión de tickets de pesadas de la bascula publica. 
---
## 📁 Estructura del Proyecto

```
AgroPeso/
├── backend/
│   ├── config/
│   │   └── database.py          # Conexión a MySQL: engine, SessionLocal, Base y get_db
│   ├── controllers/             # (reservada para futuros controladores)
│   ├── middleware/              # (reservada: JWT, logs, manejo de errores)
│   ├── models/                  # Capa de acceso a datos y dominio
│   │   ├── __init__.py
│   │   ├── products.py          # Modelo SQLAlchemy: Product
│   │   ├── suppliers.py         # Modelo SQLAlchemy: Supplier
│   │   └── ticket_model.py      # Entidad pura Ticket y modelo TicketDB
│   ├── repository/              # Capa de acceso a datos (patrón Repository)
│   │   ├── __init__.py
│   │   └── ticket_repository.py
│   ├── routers/                 # Capa de presentación: endpoints HTTP
│   │   ├── __init__.py
│   │   └── ticket_router.py
│   ├── schemas/                 # Capa de presentación: esquemas de Pydantic
│   │   ├── __init__.py
│   │   └── ticket_schema.py
│   ├── services/                # Capa de lógica de negocio
│   │   ├── __init__.py
│   │   └── ticket_service.py
│   ├── tests/                   # Pruebas con pytest
│   │   ├── test_repository.py
│   │   ├── test_schemas.py
│   │   └── test_server.py
│   ├── utils/
│   │   └── exceptions.py        # Excepciones propias (ReglaNegocioError, TicketNoEncontradoError)
│   ├── create_table.py          # Script para crear las tablas en la base de datos
│   ├── main.py                  # Punto de entrada: aplicación FastAPI
│   └── pytest.ini               # Configuración de pytest
├── frontend/
│   ├── css/
│   ├── html/
│   └── js/
├── env/                         # Entorno virtual de Python (no se versiona)
├── .env                         # Credenciales de la base de datos (no se versiona)
├── .gitignore
├── README.md
└── requirements.txt             # Dependencias de Python
```

### Responsabilidad de cada capa

| Capa | Carpetas | Responsabilidad |
|---|---|---|
| Presentación | `routers/`, `schemas/` | Recibir peticiones HTTP, validar el formato del JSON y devolver respuestas con el código correcto |
| Lógica de negocio | `services/`, entidad `Ticket` en `models/` | Aplicar las reglas del sistema, sin conocer HTTP ni la base de datos |
| Acceso a datos | `repository/`, modelos SQLAlchemy en `models/`, `config/` | Guardar y leer en MySQL, convirtiendo entre entidades y modelos de base de datos |
| Transversal | `utils/`, `middleware/` | Excepciones, logs y seguridad, usados por todas las capas |

Las dependencias van siempre hacia abajo:

```
Router  →  Service  →  Repository  →  Base de datos
```
---

## Las tres representaciones de un ticket

Cada capa de la arquitectura tiene su propia forma de ver un ticket, por eso no se reutiliza una sola clase para todo.

| Clase | Capa | Para qué sirve |
|---|---|---|
|         `TicketDB`                | Acceso a datos | Guardarse en MySQL (modelo de SQLAlchemy) |
|         `Ticket`                  |     Negocio    | Reglas y lógica (entidad pura, sin dependencias externas) |
| `TicketCreate` / `TicketResponse` |  Presentación  | Lo que entra y sale por la API (esquemas de Pydantic) |

Reglas de dependencia:

- La entidad `Ticket` no importa nada de SQLAlchemy ni de Pydantic.
- Los esquemas de Pydantic solo se usan en la capa de presentación (routers y controladores).
- Los modelos de SQLAlchemy solo se usan dentro del repositorio.
- La conversión entre una representación y otra la hace la capa que está en el límite: el repositorio convierte entre `Ticket` y `TicketDB`, y el router convierte entre los esquemas y `Ticket`.


```
Router (FastAPI)  →  TicketService  →  TicketRepository  →  MySQL
(esquemas)           (reglas)           (guardar y leer)
```

#### Campos de `TicketCreate`

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `chofer` | texto | Sí | No vacío, máximo 200 caracteres |
| `patente` | texto | No | Máximo 11 caracteres |
| `peso_tara` | entero | Sí | Mayor a 0 |
| `peso_bruto` | entero | Sí | Mayor a 0 |
| `supplier_id` | entero | Sí | Mayor a 0 |
| `product_id` | entero | No | Mayor a 0 |
| `transporte` | texto | No | Por defecto `"Equipo"`, máximo 50 caracteres |
| `numero_ticket` | entero | No | Único en la base de datos |
| `fecha` | fecha | No | Por defecto, la fecha de hoy |

`TicketResponse` incluye los mismos campos, más `id` y `peso_neto` (calculado como `peso_bruto - peso_tara`).

#### Ejemplo de solicitud

```json
{
  "chofer": "Ivan Derio",
  "patente": "HKN279",
  "peso_tara": 15160,
  "peso_bruto": 48260,
  "supplier_id": 1
}
```
---
#### Endpoints

| Método | Ruta | Descripción | Esquema de entrada | Respuesta |
|---|---|---|---|---|
| POST | `/tickets/` | Registra una pesada | `TicketCreate` | `TicketResponse` (201) |
| GET | `/tickets/{ticket_id}` | Obtiene un ticket por id | — | `TicketResponse` (200) |

#### Códigos de respuesta

| Código | Cuándo ocurre |
|---|---|
| 200 / 201 | La operación se realizó correctamente |
| 400 | Se viola una regla del negocio (por ejemplo, el peso bruto no es mayor a la tara) |
| 404 | No existe el ticket solicitado |
| 422 | El JSON no cumple el formato de los esquemas (tipos, valores negativos, campos desconocidos) |

#### Cómo ejecutar la API

Con el entorno virtual activo y el servicio de MariaDB iniciado (`sudo service mariadb start`), desde la carpeta `backend/`:

```bash
uvicorn main:app --reload
```

La documentación interactiva, donde se pueden probar los endpoints, está disponible en `/docs`.

#### Flujo completo de una petición

```
HTTP  →  Router (esquemas)  →  TicketService (reglas)  →  TicketRepository  →  MySQL
```

#### Pendientes conocidos

- Si el `supplier_id` no existe o el `numero_ticket` está repetido, MySQL rechaza la operación y la API responde 500. Falta traducirlo a un error controlado (por ejemplo, 409).
---

## Historial de tickets

### AGROPESO-001: Configuración de la conexión a MySQL

Se configuró la conexión a la base de datos MySQL usando SQLAlchemy.

- `backend/config/database.py` exporta el `engine`, `SessionLocal` (fábrica de sesiones) y `Base` (clase declarativa de la que heredan los modelos).
- Las credenciales (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`) no están escritas en el código: se leen desde un archivo `.env` con `python-dotenv`.
- El archivo `.env` está excluido del repositorio mediante `.gitignore`.
- Se usa el driver `PyMySQL` (`mysql+pymysql://`).

### AGROPESO-002: Entidad pura `Ticket` y modelo `TicketDB`

Se separó el concepto de ticket de pesaje en dos clases, dentro de `backend/models/ticket_model.py`:

- `Ticket`: entidad pura de dominio, implementada con `@dataclass`. No conoce SQLAlchemy ni MySQL. Contiene fecha, chofer, patente, peso de tara, peso bruto, proveedor, producto (opcional), transporte y número de ticket (opcional). El peso neto es una propiedad calculada (`peso_bruto - peso_tara`).
- `TicketDB`: modelo de SQLAlchemy asociado a la tabla `tickets`, con claves foráneas hacia `suppliers` y `products`. El número de ticket es único y admite valores nulos.

Se eliminó el modelo provisorio `Pesada`, que fue reemplazado por `TicketDB`. Las tablas `suppliers`, `products` y `tickets` se crean con el script `create_table.py`.

### AGROPESO-003: Repositorio de tickets (capa de acceso a datos)

Se implementó el patrón Repository en `backend/repository/ticket_repository.py`.

- `TicketRepository` recibe la sesión de SQLAlchemy por constructor.
- `create_ticket(ticket)`: recibe una entidad `Ticket`, la convierte a `TicketDB`, la guarda y devuelve un `Ticket` con el `id` asignado por la base.
- `get_ticket_by_id(ticket_id)`: devuelve un `Ticket` o `None` si no existe.
- Las conversiones entre entidad y modelo (`_to_db` y `_to_entity`) están encapsuladas en el repositorio, por lo que las capas superiores nunca manejan objetos de SQLAlchemy.
- Se corrigieron las relaciones de `Supplier` y `Product` para que apunten a `TicketDB` mediante el atributo `tickets`.

### AGROPESO-004: Servicio de tickets (capa de negocio)

Se implementó la capa de lógica de negocio en `backend/services/ticket_service.py`, que actúa como intermediaria entre los controladores de la API y el repositorio.

- `TicketService` recibe un `TicketRepository` por inyección de dependencias y no conoce SQLAlchemy ni sesiones.
- `registrar_pesada(ticket)`: valida la regla de negocio inicial (el peso bruto debe ser mayor a la tara) y, si se cumple, guarda el ticket mediante el repositorio. Si no se cumple, no se guarda nada.
- `obtener_ticket(ticket_id)`: devuelve el ticket solicitado o lanza un error si no existe.
- Se crearon excepciones propias en `backend/utils/exceptions.py`:
  - `ReglaNegocioError`: se viola una regla del negocio (se traducirá a HTTP 400).
  - `TicketNoEncontradoError`: no existe el ticket pedido (se traducirá a HTTP 404).
- Se agregaron tests con `pytest` en `backend/tests/`, que prueban el servicio con un repositorio falso (sin necesidad de base de datos). Se ejecutan desde `backend/` con el comando `pytest`.

### AGROPESO-005: Esquemas de la API (Pydantic)

Se definió la forma exacta de los datos JSON que entran y salen de la API, en `backend/schemas/ticket_schema.py`.

- `TicketCreate`: lo que el cliente envía para registrar una pesada. Valida el formato de los datos y rechaza campos desconocidos (por ejemplo, `id` o `peso_neto`, que el cliente no puede enviar).
- `TicketResponse`: lo que la API devuelve. Incluye `id` y `peso_neto`, y se construye a partir de la entidad `Ticket` devuelta por el servicio.
- Los esquemas pertenecen únicamente a la capa de presentación; ni la entidad ni el servicio los usan.
- La regla de negocio "el peso bruto debe ser mayor a la tara" se mantiene en `TicketService`. Pydantic solo valida el formato.

### AGROPESO-006: Endpoints de FastAPI (capa de presentación)

Se expusieron las funciones del servicio mediante peticiones HTTP, en `backend/routers/ticket_router.py`.

- Se definió un `APIRouter` con el prefijo `/tickets`.
- Cada endpoint recibe la sesión de base de datos con `Depends(get_db)`, instancia el `TicketRepository`, se lo pasa al `TicketService` y devuelve la respuesta con los esquemas de Pydantic.
- `get_db` (en `config/database.py`) entrega una sesión por petición y la cierra al terminar.
- `main.py` crea la aplicación FastAPI y registra el router.
- Las excepciones del servicio se traducen a códigos HTTP en el router, porque conocer HTTP es responsabilidad de esta capa.

### AGROPESO-007: Punto de entrada de la aplicación

Se configuró el archivo principal `backend/main.py`, que inicializa el servidor FastAPI.

- Crea la aplicación con `FastAPI` y registra el router de tickets con `app.include_router(ticket_router.router)`.
- Configura `CORSMiddleware` para permitir peticiones desde el frontend. El navegador bloquea las peticiones entre orígenes distintos (otro dominio o puerto) salvo que la API responda con las cabeceras CORS correspondientes. Postman, `curl` y la página `/docs` no están sujetos a esta restricción.
- Los orígenes permitidos no están escritos en el código: se leen de la variable `CORS_ORIGINS` del archivo `.env`, separados por coma.

#### Variable de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `CORS_ORIGINS` | Orígenes del frontend autorizados a llamar a la API, separados por coma y sin espacios | `http://localhost:5500,http://127.0.0.1:5500` |

Si no está definida, se usa `http://localhost:5500` por defecto. Después de modificar el `.env`, hay que reiniciar el servidor para que tome el cambio.

#### Notas

- Un origen se compone de protocolo, dominio y puerto, sin barra final. `localhost` y `127.0.0.1` son orígenes distintos para el navegador.
- En GitHub Codespaces, si el puerto 8000 tiene visibilidad privada, las peticiones del navegador que no incluyen la sesión de GitHub pueden fallar con un error de CORS aunque la configuración sea correcta.

### AGROPESO-008: Interfaz de usuario HTML con W3.CSS

Se maquetó la vista web principal para el ingreso manual de los datos de pesaje, en `frontend/html/index.html`.

- La hoja de estilos de W3.CSS se importa mediante CDN, por lo que no requiere instalación.
- El formulario contiene los campos Chofer, Patente, Peso Tara, Peso Bruto y Proveedor.
- El atributo `name` de cada input coincide con el campo correspondiente del esquema `TicketCreate` de la API, para poder armar el JSON sin traducir nombres.
- Incluye validaciones básicas del navegador (campos obligatorios, pesos mayores a 0, largos máximos). La validación real sigue siendo la de la API.
- Por ahora el formulario no envía datos: la conexión con la API se implementa en un ticket posterior.

#### Campos del formulario

| Campo | Tipo de input | Obligatorio | Campo de la API |
|---|---|---|---|
| Chofer | texto (máx. 200) | Sí | `chofer` |
| Patente | texto (máx. 11) | No | `patente` |
| Peso tara (kg) | número, mínimo 1 | Sí | `peso_tara` |
| Peso bruto (kg) | número, mínimo 1 | Sí | `peso_bruto` |
| Proveedor | lista desplegable | Sí | `supplier_id` |

#### Cómo visualizar la página

Desde la carpeta `frontend/html/`:

```bash
python3 -m http.server 5500
```

También se puede abrir con la extensión *Live Server* de VS Code (puerto 5500). En GitHub Codespaces, la página se abre desde la pestaña *Ports*.

#### Pendientes conocidos

- La lista de proveedores es provisoria (una opción fija). Se cargará dinámicamente cuando exista un endpoint para listar proveedores.
- Los campos opcionales de la API (`product_id`, `transporte`, `numero_ticket`, `fecha`) todavía no están en el formulario.
- En Codespaces, la dirección del frontend debe agregarse a `CORS_ORIGINS` en el `.env` para que el navegador permita las llamadas a la API.

## Entorno de desarrollo (GitHub Codespaces)

- El servidor de base de datos es MariaDB, instalado dentro del Codespace (`sudo apt install mariadb-server`).
- Al reabrir el Codespace hay que iniciar el servicio: `sudo service mariadb start`.
- Base de datos: `AgroPeso`, con un usuario dedicado configurado en el `.env`.
- Entorno virtual: `source env/bin/activate`. Dependencias en `requirements.txt`.
- Los scripts se ejecutan desde la carpeta `backend/`.
- Tests: `pytest` (ejecutar desde `backend/`; configuración en `pytest.ini`).
