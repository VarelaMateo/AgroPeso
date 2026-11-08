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

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| GET | `/tickets/` | Lista los tickets, los más recientes primero. Filtro opcional `?estado=abierto` o `?estado=cerrado` | `list[TicketResponse]` (200) |
| PATCH | `/tickets/{ticket_id}/cerrar` | Registra la segunda pesada y cierra el ticket | `TicketResponse` (200) |

`POST /tickets/` ahora acepta pesadas sin `peso_bruto` (queda abierto) o con `peso_bruto` (queda cerrado).

#### Códigos de respuesta

| Código | Cuándo ocurre |
|---|---|
| 200 / 201 | La operación se realizó correctamente |
| 400 | Se viola una regla del negocio (por ejemplo, el peso bruto no es mayor a la tara) |
| 404 | No existe el ticket solicitado |
| 422 | El JSON no cumple el formato de los esquemas (tipos, valores negativos, campos desconocidos) |
|---|---|
| 400 | Al cerrar: el ticket ya está cerrado, o el peso bruto no es mayor a la tara |
| 404 | Al cerrar: el ticket no existe |
| 422 | `?estado=` con un valor que no es `abierto` ni `cerrado`, o `peso_bruto` menor o igual a 0 al cerrar |

#### Ejemplos

Abrir un ticket (`POST /tickets/`, sin `peso_bruto`):

```json
{
  "chofer": "Ivan Derio",
  "patente": "HKN279",
  "peso_tara": 15160,
  "supplier_id": 1
}
```

Respuesta (201):

```json
{
  "chofer": "Ivan Derio",
  "patente": "HKN279",
  "peso_tara": 15160,
  "peso_bruto": null,
  "supplier_id": 1,
  "product_id": null,
  "transporte": "Equipo",
  "numero_ticket": null,
  "id": 1,
  "fecha": "2026-11-07",
  "estado": "abierto",
  "peso_neto": null
}
```

Cerrar el ticket (`PATCH /tickets/1/cerrar`):

```json
{
  "peso_bruto": 48260
}
```

La respuesta (200) devuelve el ticket con `"estado": "cerrado"`, `"peso_bruto": 48260` y `"peso_neto": 33100`.

Listar solo los tickets abiertos: `GET /tickets/?estado=abierto`.

#### Actualizar una base de datos existente

`create_table.py` crea las tablas desde cero con la columna `estado`. Si la tabla `tickets` ya existía, hay que modificarla a mano (`create_all` no altera tablas existentes). Los tickets ya cargados se marcan como cerrados:

```bash
sudo mysql AgroPeso -e "
ALTER TABLE tickets
  MODIFY peso_bruto INT NULL,
  MODIFY peso_neto INT NULL,
  ADD COLUMN estado VARCHAR(10) NOT NULL DEFAULT 'abierto';
UPDATE tickets SET estado = 'cerrado' WHERE peso_bruto IS NOT NULL;"
```

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

#### Estados del ticket

| Estado | Significado | Datos |
|---|---|---|
| `abierto` | Se registró solo la primera pesada (la tara) | `peso_bruto` y `peso_neto` vacíos (`null`) |
| `cerrado` | Se registró la segunda pesada (el peso bruto) | `peso_neto = peso_bruto - peso_tara` |

Reglas de negocio (en `TicketService`):

- La primera pesada es la tara. El estado lo decide el servicio y el cliente no puede enviarlo (la API responde 422).
- Al registrar una pesada sin `peso_bruto`, el ticket queda abierto. Si se envía `peso_bruto`, se valida que sea mayor a la tara y el ticket queda cerrado.
- Un ticket solo se puede cerrar si existe, está abierto y el peso bruto es mayor a la tara.


#### Pendientes conocidos

- Si el `supplier_id` no existe o el `numero_ticket` está repetido, MySQL rechaza la operación y la API responde 500. Falta traducirlo a un error controlado (por ejemplo, 409).
- La interfaz web todavía envía siempre tara y bruto, por lo que crea tickets cerrados. Falta una pantalla para abrir un ticket y cerrarlo después.
- Se asume que la primera pesada es la tara. Si hay operaciones donde el camión llega cargado, habrá que revisar este supuesto.
- El listado trae todos los tickets. Más adelante conviene paginarlo (`limit` y `offset`).
- Los cambios en las tablas se hacen con `ALTER TABLE` manual. A futuro conviene usar migraciones con Alembic.
---

#### Tests

Se reescribieron con `pytest` (se ejecutan con `pytest` desde `backend/`):

- `test_schemas.py`: validaciones de los esquemas.
- `test_server.py`: reglas del servicio, con un repositorio en memoria (sin base de datos).
- `test_repository.py`: repositorio contra la base real. Usa las fixtures de `conftest.py`, que deshacen los cambios al terminar, por lo que requiere MariaDB encendido y no deja datos de prueba.

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

Desde la carpeta `frontend/`:

```bash
python3 -m http.server 5500
```

y abrir `http://localhost:5500/html/index.html`. También se puede abrir con la extensión *Live Server* de VS Code (puerto 5500). En GitHub Codespaces, la página se abre desde la pestaña *Ports*.

#### Pendientes conocidos

- La lista de proveedores es provisoria (una opción fija). Se cargará dinámicamente cuando exista un endpoint para listar proveedores.
- Los campos opcionales de la API (`product_id`, `transporte`, `numero_ticket`, `fecha`) todavía no están en el formulario.
- En Codespaces, la dirección del frontend debe agregarse a `CORS_ORIGINS` en el `.env` para que el navegador permita las llamadas a la API.

### AGROPESO-009: Conexión Frontend-Backend (JavaScript)

Se conectó el formulario HTML con la API mediante JavaScript, en `frontend/js/app.js`. El script se vincula al final de `index.html` con `<script src="../js/app.js"></script>`, para que el formulario ya exista cuando se ejecute.

#### Funcionamiento

1. **Intercepta el envío del formulario.** Con `event.preventDefault()` se evita que el navegador recargue la página.
2. **Construye el objeto JSON** a partir de los campos del formulario. Como cada input tiene un `name` igual al campo de `TicketCreate`, no hace falta traducir nombres:
   - `peso_tara`, `peso_bruto` y `supplier_id` se convierten a número, porque los inputs entregan texto y la API rechaza un texto donde espera un entero.
   - Una patente vacía se envía como `null`, que es lo que representa "sin patente" en el esquema.
3. **Envía un `POST`** a `http://127.0.0.1:8000/tickets/` con `fetch()`, con la cabecera `Content-Type: application/json`.
4. **Muestra el resultado** en el panel de mensajes del formulario.

#### Resultados que muestra la interfaz

| Situación | Código HTTP | Mensaje mostrado |
|---|---|---|
| Pesada registrada | 201 | Panel verde con el ID y el peso neto devueltos por la API. El formulario se vacía |
| Se viola una regla del negocio (por ejemplo, bruto menor o igual a la tara) | 400 | Panel rojo con el mensaje del servicio |
| Los datos no cumplen el formato del esquema | 422 | Panel rojo con el campo y el motivo del rechazo |
| Error interno del servidor (por ejemplo, proveedor inexistente) | 500 | Panel rojo con un mensaje genérico con el código de error |
| La API no está encendida o no es alcanzable | — | Panel rojo: "No se pudo conectar con el servidor" |

#### Detalles de implementación

- **Dos tipos de fallo.** Si la API responde con un error HTTP, `fetch()` no lanza una excepción: hay que revisar `respuesta.ok`. Solo cuando no hay conexión se lanza una excepción, que se atrapa con `try/catch`.
- **Mensajes de error.** El campo `detail` de la respuesta es un texto en los errores 400 y 404, y una lista de objetos en los errores 422. La función `textoDeError` unifica los dos formatos.
- **Seguridad.** Los mensajes se muestran con `textContent` y no con `innerHTML`, de modo que cualquier texto recibido se muestra como texto y no se interpreta como HTML.
- **Envíos duplicados.** El botón se deshabilita mientras se procesa la petición y se vuelve a habilitar en el bloque `finally`, ocurra lo que ocurra.

#### Cómo ejecutar y probar

1. Iniciar la base de datos: `sudo service mariadb start`.
2. Iniciar la API, desde `backend/`:

   ```bash
   uvicorn main:app --reload
   ```

3. Servir el frontend, desde la carpeta **`frontend/`** (no desde `frontend/html/`, porque el HTML necesita llegar a `../js/app.js`):

   ```bash
   cd frontend
   python3 -m http.server 5500
   ```

4. Abrir `http://localhost:5500/html/index.html`.

Para verificar que la pesada se guardó en la base:

```bash
sudo mysql AgroPeso -e "SELECT id, fecha, chofer, peso_tara, peso_bruto, peso_neto FROM tickets;"
```

#### Casos de prueba

| Prueba | Resultado esperado |
|---|---|
| Datos válidos | Mensaje verde con ID y peso neto. La fila aparece en la tabla `tickets` |
| Tara mayor que el bruto | Mensaje rojo con la regla de negocio |
| API apagada (`Ctrl+C` en uvicorn) | Mensaje rojo de falta de conexión |

#### Configuración según el entorno

- La URL de la API está definida en la constante `API_URL` de `app.js`. Si el frontend se abre desde una dirección distinta a `localhost` (por ejemplo, una URL de GitHub Codespaces), hay que reemplazarla por la dirección pública del puerto 8000.
- El origen desde el cual se abre el frontend (protocolo, dominio y puerto, sin barra final) debe estar incluido en `CORS_ORIGINS` del `.env`, y hay que reiniciar la API después de modificarlo.
- En Codespaces, si el puerto 8000 tiene visibilidad privada, el navegador puede recibir un error de CORS aunque la configuración sea correcta. Para probar, se puede cambiar temporalmente a visibilidad pública (volviendo a privada al terminar).

#### Diagnóstico de problemas

Con las herramientas del navegador (`F12`):

- **Console**: muestra errores de JavaScript y de CORS.
- **Network**: muestra la petición enviada, su código de respuesta y el cuerpo.
- Si al enviar el formulario la URL cambia (aparecen los datos como parámetros) o no aparece ningún mensaje, el script no se cargó: revisar la ruta del `<script>` y que la página se abra desde `/html/index.html`.

#### Pendientes conocidos

- Si el `supplier_id` no existe o el `numero_ticket` está repetido, la API responde 500 y la interfaz muestra un error genérico. Falta traducirlo a un error controlado (409) con un mensaje claro.
- La lista de proveedores sigue siendo provisoria, hasta contar con un endpoint para listarlos.

### AGROPESO-010: Listado de tickets y flujo de tickets abiertos y cerrados

Se creó el endpoint para listar el historial de pesadas, con filtro opcional por estado. Para poder filtrar se incorporó el concepto de **estado del ticket**, que permite registrar una pesada en dos momentos: la primera pesada abre el ticket y la segunda lo cierra.

#### Cambios por capa

| Capa | Archivo | Cambio |
|---|---|---|
| Dominio y datos | `models/ticket_model.py` | Enumeración `EstadoTicket`, campo `estado` en `Ticket` y `TicketDB`. `peso_bruto` y `peso_neto` admiten nulos |
| Acceso a datos | `repository/ticket_repository.py` | `get_all_tickets(estado=None)` y `update_ticket(ticket)` |
| Negocio | `services/ticket_service.py` | `obtener_todos_los_tickets(estado=None)`, `cerrar_ticket(ticket_id, peso_bruto)` y validación de pesos compartida |
| Presentación | `schemas/ticket_schema.py` | `peso_bruto` opcional, `estado` en `TicketResponse` y nuevo esquema `TicketClose` |
| Presentación | `routers/ticket_router.py` | `GET /tickets/` y `PATCH /tickets/{ticket_id}/cerrar` |

### AGROPESO-012: Interfaz del historial (HTML + JS)

Se agregó a la interfaz web una tabla con los tickets registrados, que consume el endpoint `GET /tickets/`.

- **`frontend/html/index.html`**: nueva sección debajo del formulario, con una tabla de W3.CSS (`w3-table-all`, con scroll horizontal en pantallas chicas). Tiene su propio contenedor, más ancho que el del formulario, para que las columnas no queden apretadas.
- **`frontend/js/app.js`**: la función `cargarHistorial()` hace un `fetch()` GET a la API y dibuja las filas de la tabla de forma dinámica.

#### Cuándo se carga

- Al abrir la página.
- Cada vez que se registra una pesada desde el formulario, para que el nuevo ticket aparezca sin recargar.

#### Columnas

| Columna | Campo de la API | Formato |
|---|---|---|
| ID | `id` | Número |
| Fecha | `fecha` | `día/mes/año` |
| Chofer | `chofer` | Texto |
| Patente | `patente` | Texto, o `—` si no tiene |
| Proveedor (ID) | `supplier_id` | Número |
| Tara (kg) | `peso_tara` | Con separador de miles |
| Bruto (kg) | `peso_bruto` | Con separador de miles, o `—` si el ticket está abierto |
| Neto (kg) | `peso_neto` | Con separador de miles, o `—` si el ticket está abierto |
| Estado | `estado` | Etiqueta de color: naranja (`abierto`) o verde (`cerrado`) |

Los tickets se muestran del más reciente al más antiguo, que es el orden en que los devuelve la API.

#### Mensajes de la tabla

| Situación | Lo que se muestra |
|---|---|
| Mientras carga | "Cargando..." |
| No hay tickets en la base | "Todavía no hay pesadas registradas" |
| La API no responde o devuelve un error | "No se pudo cargar el historial. ¿Está encendida la API?" (el detalle del error queda en la consola del navegador) |

#### Detalles de implementación

- Las filas se construyen con `createElement` y `textContent`, no con `innerHTML`, de modo que cualquier texto recibido (por ejemplo, un nombre de chofer) se muestra como texto y no se interpreta como HTML.
- Para vaciar y volver a llenar la tabla se usa `replaceChildren()`, que reemplaza todas las filas de una vez. No confundir con `replaceChild()`, que reemplaza un único hijo y falla si no se le indica cuál.
- El navegador exige que el origen desde el que se abre el frontend esté incluido en `CORS_ORIGINS` del `.env`. `http://localhost:5500` y `http://127.0.0.1:5500` son orígenes distintos, por lo que conviene incluir ambos. Después de modificar el `.env` hay que reiniciar la API por completo, ya que `--reload` no vigila ese archivo.

#### Cómo probarlo

1. Iniciar MariaDB y la API (`uvicorn main:app --reload`, desde `backend/`).
2. Servir el frontend desde la carpeta `frontend/` con `python3 -m http.server 5500`.
3. Abrir `http://localhost:5500/html/index.html`.

| Prueba | Resultado esperado |
|---|---|
| Abrir la página | La tabla muestra los tickets existentes, los más nuevos arriba |
| Un ticket abierto | Etiqueta naranja y `—` en bruto y neto |
| Registrar una pesada desde el formulario | Aparece arriba en la tabla sin recargar la página |
| Apagar la API y recargar | Fila con el mensaje de que no se pudo cargar el historial |

#### Pendientes conocidos

- La columna de proveedor muestra el ID, porque la API de tickets devuelve solo `supplier_id`. Para mostrar el nombre hace falta un endpoint de proveedores.
- La tabla muestra todos los tickets. Más adelante conviene paginarla y agregar un filtro por estado (la API ya lo soporta con `?estado=abierto` o `?estado=cerrado`).
- Desde la interfaz todavía no se puede cerrar un ticket abierto (el endpoint `PATCH /tickets/{ticket_id}` ya existe, falta la pantalla).
- No hay tests automáticos del router ni del frontend, y un error de nombres como el de `obtener_todos_los_tickets` solo se detectó al probar a mano.

### AGROPESO-013: Endpoints de proveedores (backend)

Se implementó el flujo completo (esquemas, repositorio, servicio y router) para listar y crear proveedores, de modo que el frontend pueda dejar de usar una lista fija.

#### Archivos

| Capa | Archivo | Contenido |
|---|---|---|
| Dominio y datos | `models/suppliers.py` | Entidad pura `SupplierEntity` y modelo `Supplier` de SQLAlchemy |
| Presentación | `schemas/supplier_schema.py` | `SupplierCreate` y `SupplierResponse` |
| Acceso a datos | `repository/supplier_repository.py` | `get_all_suppliers()` y `create_supplier()` |
| Negocio | `services/supplier_service.py` | `obtener_todos_los_proveedores()` y `crear_proveedor()` |
| Presentación | `routers/supplier_router.py` | `GET /suppliers/` y `POST /suppliers/`, registrado en `main.py` |

#### Endpoints

| Método | Ruta | Descripción | Esquema de entrada | Respuesta |
|---|---|---|---|---|
| GET | `/suppliers/` | Lista los proveedores, ordenados por nombre | — | `list[SupplierResponse]` (200) |
| POST | `/suppliers/` | Crea un proveedor | `SupplierCreate` | `SupplierResponse` (201) |

#### Esquemas

| Esquema | Campo | Tipo | Regla |
|---|---|---|---|
| `SupplierCreate` | `name` | texto | Obligatorio, se eliminan los espacios de los extremos, no puede quedar vacío, máximo 200 caracteres. No admite campos extra |
| `SupplierResponse` | `id` | entero | Asignado por la base de datos |
| `SupplierResponse` | `name` | texto | Nombre del proveedor |

Ejemplo (`POST /suppliers/`):

```json
{
  "name": "Berg"
}
```

Respuesta (201):

```json
{
  "id": 1,
  "name": "Berg"
}
```

#### Códigos de respuesta

| Código | Cuándo ocurre |
|---|---|
| 200 | Listado correcto (devuelve `[]` si no hay proveedores) |
| 201 | Proveedor creado |
| 422 | El nombre falta, está vacío o supera los 200 caracteres, o se envían campos que no corresponden |

#### Decisiones de diseño

- El campo se llama `name` (y no `nombre`) para coincidir con el modelo de la base de datos y evitar traducciones entre capas.
- Se creó la entidad pura `SupplierEntity`, de modo que el repositorio devuelva entidades y nunca objetos de SQLAlchemy, igual que con los tickets. Se llama así porque `Supplier` ya es el modelo de la tabla.
- Solo se maneja el nombre. Las columnas `cuit` y `phone` quedan vacías, y `fecha_alta` la completa la base de datos.

#### Tests

`tests/test_suppliers.py` cubre los esquemas, el servicio (con un repositorio en memoria) y el repositorio contra la base real (con las fixtures de `conftest.py`, que deshacen los cambios al terminar).

#### Pendientes conocidos

- El formulario del frontend todavía usa una lista fija de proveedores; falta que cargue las opciones desde `GET /suppliers/` y que la tabla del historial muestre el nombre en lugar del ID.
- No se valida que el nombre sea único: se pueden crear dos proveedores con el mismo nombre.
- No hay endpoints para obtener, editar ni eliminar un proveedor individual, ni se pueden cargar `cuit` y `phone`.
- Un `supplier_id` inexistente al registrar una pesada sigue devolviendo 500.

## Entorno de desarrollo (GitHub Codespaces)

- El servidor de base de datos es MariaDB, instalado dentro del Codespace (`sudo apt install mariadb-server`).
- Al reabrir el Codespace hay que iniciar el servicio: `sudo service mariadb start`.
- Base de datos: `AgroPeso`, con un usuario dedicado configurado en el `.env`.
- Entorno virtual: `source env/bin/activate`. Dependencias en `requirements.txt`.
- Los scripts se ejecutan desde la carpeta `backend/`.
- Tests: `pytest` (ejecutar desde `backend/`; configuración en `pytest.ini`).
