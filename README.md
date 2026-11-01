# AgroPeso
Es una plataforma web para la gestión de tickets de pesadas de la bascula publica. 
---
## 📁 Estructura del Proyecto

```text
AgroPeso/
├── .env                       # credenciales (nuevo, lo creás vos)
├── .gitignore
├── requirements.txt
├── env/                       # entorno virtual (no se toca a mano)
└── backend/
    ├── tests/
    │   ├── test_service.py
    │   └── test_repository.py
    ├── config/
    │   ├── __init__.py
    │   └── database.py        # engine, SessionLocal, Base
    ├── models/
    │   ├── __init__.py
    │   ├── supplier.py        # class Supplier
    │   ├── product.py         # class Product
    │   └── pesada.py          # class Pesada
    ├── repository/
    │   └── pesada_repository.py
    ├── services/
    │   └── pesada_service.py
    ├── controllers/           # reciben la petición y llaman al servicio
    ├── routers/               # definen las rutas (/pesadas, etc.)
    ├── middleware/            # JWT, logs
    └── utils/                 # funciones auxiliares (hash de contraseñas, etc.)
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

## Entorno de desarrollo (GitHub Codespaces)

- El servidor de base de datos es MariaDB, instalado dentro del Codespace (`sudo apt install mariadb-server`).
- Al reabrir el Codespace hay que iniciar el servicio: `sudo service mariadb start`.
- Base de datos: `AgroPeso`, con un usuario dedicado configurado en el `.env`.
- Entorno virtual: `source env/bin/activate`. Dependencias en `requirements.txt`.
- Los scripts se ejecutan desde la carpeta `backend/`.
- Tests: `pytest` (ejecutar desde `backend/`; configuración en `pytest.ini`).
